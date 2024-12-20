from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import joinedload, selectinload
from app.models import Document, ChunkOllama, ChunkOpenAI, Collection
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT
from app.core.config import settings, EmbeddingProvider
from app.services.embeddings import get_embeddings
from app.services.pdf_processor import process_pdf
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_document(
        self, 
        file_content: bytes, 
        filename: str, 
        collection_id: str,
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> Tuple[int, int]:
        logger.info(f"Processing document: {filename} for collection: {collection_id}")
        # Use default values from settings if not provided
        chunk_size = chunk_size or settings.CHUNK_SIZE
        chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        try:
            # Process file based on type
            if isinstance(file_content, bytes):
                if file_content.startswith(b'%PDF'):
                    chunks_with_pages = process_pdf(file_content)
                    if not chunks_with_pages:
                        logger.error("Could not extract text from PDF")
                        raise ValueError("Could not extract text from PDF")
                else:
                    # Process text or markdown file
                    text_content = file_content.decode('utf-8', errors='replace')
                    # Split into chunks with specified size and overlap
                    chunks = []
                    current_pos = 0
                    while current_pos < len(text_content):
                        chunk_end = min(current_pos + chunk_size, len(text_content))
                        # If we're not at the end, find the last space to break at
                        if chunk_end < len(text_content):
                            last_space = text_content.rfind(' ', current_pos, chunk_end)
                            if last_space != -1:
                                chunk_end = last_space
                        chunks.append(text_content[current_pos:chunk_end].strip())
                        # Move position considering overlap
                        current_pos = max(current_pos + 1, chunk_end - chunk_overlap)
                    chunks_with_pages = [(chunk, 1) for chunk in chunks if chunk]  # All chunks are "page 1" for text files
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding text file: {e}")
            raise ValueError("Invalid text file encoding. Please ensure the file is UTF-8 encoded.")

        # Check if collection exists
        result = await self.db.execute(
            select(Collection).where(Collection.name == collection_id)
        )
        collection = result.scalar_one_or_none()
        if not collection:
            logger.error(f"Collection not found: {collection_id}")
            raise ValueError(f"Collection not found: {collection_id}")

        # Check for existing document
        result = await self.db.execute(
            select(Document).where(
                Document.filename == filename,
                Document.collection_id == collection.id
            )
        )
        existing_doc = result.scalar_one_or_none()
        
        if existing_doc:
            logger.info(f"Existing document found. ID: {existing_doc.id}")
            # Delete existing chunks
            if settings.EMBEDDING_PROVIDER == EmbeddingProvider.OLLAMA:
                await self.db.execute(
                    delete(ChunkOllama).where(ChunkOllama.document_id == existing_doc.id)
                )
            elif settings.EMBEDDING_PROVIDER == EmbeddingProvider.OPENAI:
                await self.db.execute(
                    delete(ChunkOpenAI).where(ChunkOpenAI.document_id == existing_doc.id)
                )
            document = existing_doc
        else:
            # Create new document
            document = Document(filename=filename, collection_id=collection.id)
            self.db.add(document)
            await self.db.flush()
        
        # Process chunks and create embeddings
        chunk_texts = [chunk_text for chunk_text, _ in chunks_with_pages]
        embeddings = await get_embeddings(chunk_texts)

        # Store chunks with embeddings
        for idx, ((chunk_text, page_num), embedding) in enumerate(zip(chunks_with_pages, embeddings)):
            logger.debug(f"Embedding for chunk {idx}: {embedding[:5]}...")  # Log first 5 elements of each embedding
            
            chunk_class = ChunkOllama if settings.EMBEDDING_PROVIDER == EmbeddingProvider.OLLAMA else ChunkOpenAI
            chunk = chunk_class(
                document_id=document.id,
                content=chunk_text,
                content_vector=embedding,
                chunk_index=idx,
                page_number=page_num
            )
            self.db.add(chunk)
        
        logger.debug(f"Processed {len(chunks_with_pages)} chunks with embeddings")
        
        await self.db.commit()
        
        return document.id, len(chunks_with_pages)

    async def get_documents(self) -> List[dict]:
        try:
            query = select(Document).options(
                joinedload(Document.collection),
                selectinload(Document.chunks_ollama),
                selectinload(Document.chunks_openai)
            )
            result = await self.db.execute(query)
            documents = result.scalars().all()
            return [{
                "id": doc.id,
                "filename": doc.filename,
                "collection_id": doc.collection_id,
                "collection_name": doc.collection.name if doc.collection else "Default",
                "chunk_count": max(len(doc.chunks_ollama or []), len(doc.chunks_openai or []), 1)
            } for doc in documents]
        except Exception as e:
            logger.error(f"Error fetching documents: {e}")
            raise
