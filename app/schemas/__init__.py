from pydantic import BaseModel
from typing import List, Optional

class DocumentBase(BaseModel):
    filename: str
    collection_id: int

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    collection_name: str
    chunk_count: int

    class Config:
        orm_mode = True

class CollectionCreate(BaseModel):
    name: str

class Collection(CollectionCreate):
    id: int

    class Config:
        orm_mode = True

class ChunkBase(BaseModel):
    content: str
    chunk_index: int
    page_number: int

class ChunkCreate(ChunkBase):
    document_id: int
    content_vector: List[float]

class Chunk(ChunkBase):
    id: int
    document_id: int
    embedding_preview: List[float]

    class Config:
        orm_mode = True

class DocumentWithChunks(Document):
    chunks: List[Chunk]

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: int
    chunks_created: int
