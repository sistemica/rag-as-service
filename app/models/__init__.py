from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import declarative_base, relationship
from app.core.config import settings
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Collection(Base):
    __tablename__ = 'collections'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    documents = relationship("Document", back_populates="collection")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    collection_id = Column(Integer, ForeignKey('collections.id', ondelete='CASCADE'))
    created_at = Column(DateTime, server_default=func.now())
    collection = relationship("Collection", back_populates="documents")
    chunks_ollama = relationship("ChunkOllama", back_populates="document", cascade="all, delete-orphan")
    chunks_openai = relationship("ChunkOpenAI", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        {'extend_existing': True},
    )

class ChunkOllama(Base):
    __tablename__ = 'chunks_ollama'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'))
    content = Column(Text, nullable=False)
    content_vector = Column(Vector(768), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    document = relationship("Document", back_populates="chunks_ollama")

class ChunkOpenAI(Base):
    __tablename__ = 'chunks_openai'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'))
    content = Column(Text, nullable=False)
    content_vector = Column(Vector(1536), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    document = relationship("Document", back_populates="chunks_openai")
