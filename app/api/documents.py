from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Depends, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, Float, union
from app.db.database import get_db
from app.services.document_service import DocumentService
from app.models import Collection, Document, ChunkOllama, ChunkOpenAI, Vector
from sqlalchemy.orm import joinedload
import logging
from typing import Optional, List, Dict
from app.services.embeddings import get_embeddings
from app.core.config import settings, EmbeddingProvider

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/query")
async def query_documents(
    query: Dict[str, str] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        query_text = query.get("query").strip().lower()
        collection_name = query.get("collection", "Default")

        if not query_text:
            raise HTTPException(status_code=400, detail="Query text is required")

        # Log the search query for debugging
        logger.debug(f"Searching for: '{query_text}' in collection: {collection_name if collection_name != '-' else 'all collections'}")

        # Get the embedding for the query
        query_embedding = await get_embeddings([query_text])
        if not query_embedding or len(query_embedding) == 0:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")

        query_embedding = query_embedding[0]

        # Select the appropriate chunk table based on the embedding provider
        chunk_table = ChunkOllama if settings.EMBEDDING_PROVIDER == EmbeddingProvider.OLLAMA else ChunkOpenAI

        # First get exact text matches
        text_matches_query = (
            select(
                chunk_table.content,
                chunk_table.chunk_index,
                Document.filename,
                Collection.name.label('collection_name'),
                func.cast(0.0, Float).label("distance")  # Give text matches a distance of 0
            )
            .select_from(chunk_table)
            .join(Document, chunk_table.document_id == Document.id)
            .join(Collection, Document.collection_id == Collection.id)
        )

        # Add collection filter only if not searching all collections
        if collection_name != '-':
            text_matches_query = text_matches_query.where(Collection.name == collection_name)
        
        # Add content search condition
        text_matches = text_matches_query.where(
            func.lower(chunk_table.content).op('~*')(f'\\y{query_text}\\y')
        )

        # Then get vector similarity matches
        vector_matches_query = (
            select(
                chunk_table.content,
                chunk_table.chunk_index,
                Document.filename,
                Collection.name.label('collection_name'),
                func.l2_distance(chunk_table.content_vector, func.cast(query_embedding, Vector)).label("distance")
            )
            .select_from(chunk_table)
            .join(Document, chunk_table.document_id == Document.id)
            .join(Collection, Document.collection_id == Collection.id)
        )

        # Add collection filter only if not searching all collections
        if collection_name != '-':
            vector_matches_query = vector_matches_query.where(Collection.name == collection_name)
        
        vector_matches = vector_matches_query.order_by("distance").limit(5)

        # Combine results with text matches first, then vector matches
        results = await db.execute(
            union(text_matches, vector_matches)
            .order_by("distance")
            .limit(5)
        )

        search_results = []
        for row in results:
            distance = row.distance
            if hasattr(distance, 'to_list'):
                distance = distance.to_list()[0] if distance.to_list() else 0.0
            elif isinstance(distance, (list, tuple)):
                distance = distance[0] if distance else 0.0
            elif isinstance(distance, str):
                try:
                    distance = float(distance)
                except ValueError:
                    distance = 0.0
            else:
                try:
                    distance = float(distance)
                except (TypeError, ValueError):
                    logger.warning(f"Unexpected distance type: {type(distance)}. Using default value.")
                    distance = 0.0

            logger.debug(f"Raw distance: {row.distance}, Processed distance: {distance}")

            search_results.append({
                "chunk_content": row.content,
                "document_filename": row.filename,
                "collection_name": row.collection_name,
                "distance": distance,
                "chunk_number": row.chunk_index
            })

        logger.debug(f"Search results: {search_results}")

        return search_results

    except Exception as e:
        logger.error(f"Error performing vector search: {e}")
        raise HTTPException(status_code=500, detail=f"Error performing vector search: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Delete associated chunks
        await db.execute(delete(ChunkOllama).where(ChunkOllama.document_id == document_id))
        await db.execute(delete(ChunkOpenAI).where(ChunkOpenAI.document_id == document_id))
        
        # Delete the document
        result = await db.execute(delete(Document).where(Document.id == document_id))
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/documents/upload/text", status_code=201)
async def upload_text_document(
    content: str = Body(..., media_type="text/plain"),
    collection_name: Optional[str] = Header(None, alias="Collection-Name", description="Collection Name"),
    document_name: Optional[str] = Header(None, alias="Document-Name", description="Document Name"),
    db: AsyncSession = Depends(get_db)
):
    if not collection_name:
        raise HTTPException(status_code=400, detail="No Collection-Name provided in header")
    
    if not document_name:
        raise HTTPException(status_code=400, detail="No Document-Name provided in header")

    try:
        document_service = DocumentService(db)
        document_id, chunks_created = await document_service.upload_document(
            content.encode('utf-8'),
            document_name,
            collection_name
        )
        
        return {
            "message": "Document uploaded successfully",
            "document_id": document_id,
            "chunks_created": chunks_created
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error processing text document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(document_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Fetch the document with its chunks
        query = select(Document).options(
            joinedload(Document.chunks_ollama),
            joinedload(Document.chunks_openai)
        ).where(Document.id == document_id)
        result = await db.execute(query)
        document = result.unique().scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Determine which chunks to use based on the embedding provider
        chunks = document.chunks_ollama if document.chunks_ollama else document.chunks_openai

        # Format the chunks data
        chunks_data = []
        for chunk in chunks:
            chunk_text = chunk.content
            chunk_start = chunk_text[:50]  # First 50 characters
            chunk_end = chunk_text[-50:]   # Last 50 characters
            
            # Safely handle the content_vector
            embedding_preview = []
            if chunk.content_vector is not None:
                if isinstance(chunk.content_vector, (list, tuple)):
                    embedding_preview = chunk.content_vector[:5]
                elif hasattr(chunk.content_vector, 'to_list'):
                    embedding_preview = chunk.content_vector.to_list()[:5]
                elif isinstance(chunk.content_vector, str):
                    try:
                        embedding_preview = eval(chunk.content_vector)[:5]
                    except:
                        logger.warning(f"Failed to parse content_vector string: {chunk.content_vector[:100]}...")
                elif hasattr(chunk.content_vector, 'tolist'):  # For numpy arrays
                    embedding_preview = chunk.content_vector.tolist()[:5]
                else:
                    logger.warning(f"Unexpected content_vector type: {type(chunk.content_vector)}")
                    try:
                        embedding_preview = list(chunk.content_vector)[:5]
                    except:
                        logger.error(f"Failed to convert content_vector to list: {chunk.content_vector}")
            
            # Ensure all elements in embedding_preview are float
            embedding_preview = [float(x) for x in embedding_preview if x is not None][:5]

            chunks_data.append({
                "chunk_number": chunk.chunk_index,
                "chunk_start": chunk_start,
                "chunk_end": chunk_end,
                "embedding_preview": embedding_preview
            })

        response_data = {
            "document_id": document.id,
            "filename": document.filename,
            "chunks": chunks_data
        }
        logger.debug(f"Chunks data for document {document_id}: {response_data}")
        return response_data
    except Exception as e:
        logger.error(f"Error fetching document chunks: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: Optional[str] = Header(None, alias="Collection-Name", description="Collection Name"),
    db: AsyncSession = Depends(get_db)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not collection_name:
        raise HTTPException(status_code=400, detail="No Collection-Name provided in header")

    if not file.filename or not (file.filename.lower().endswith('.pdf') or 
                                file.filename.lower().endswith('.txt') or 
                                file.filename.lower().endswith('.md')):
        raise HTTPException(status_code=400, detail="Only PDF, TXT, and MD files are supported")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file provided")

        # Check if it's a PDF or text file
        if file.filename.lower().endswith('.pdf') and not content.startswith(b'%PDF'):
            raise HTTPException(status_code=400, detail="Invalid PDF file")

        document_service = DocumentService(db)
        document_id, chunks_created = await document_service.upload_document(content, file.filename, collection_name)
        
        return {
            "message": "Document uploaded successfully",
            "document_id": document_id,
            "chunks_created": chunks_created
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/documents", response_model=List[dict])
async def get_documents(db: AsyncSession = Depends(get_db)):
    try:
        document_service = DocumentService(db)
        documents = await document_service.get_documents()
        return documents
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")
