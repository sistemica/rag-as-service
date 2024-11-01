from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete
from app.db.database import get_db
from app.models import Collection, Document, ChunkOllama, ChunkOpenAI
import logging
from typing import List
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

class CollectionCreate(BaseModel):
    name: str

@router.get("/collections", response_model=List[str])
async def get_collections(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Collection.name))
        collections = result.scalars().all()
        
        if not collections:
            # If no collections exist, create the default collection
            await db.execute(insert(Collection).values(name="Default"))
            await db.commit()
            collections = ["Default"]
        
        return collections
    except Exception as e:
        logger.error(f"Error fetching collections: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/collections")
async def create_collection(collection: CollectionCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_collection = Collection(name=collection.name)
        db.add(new_collection)
        await db.commit()
        return {"message": f"Collection '{collection.name}' created successfully"}
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str, db: AsyncSession = Depends(get_db)):
    try:
        # Find the collection
        result = await db.execute(select(Collection).where(Collection.name == collection_name))
        collection = result.scalar_one_or_none()
        
        if not collection:
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
        
        # Delete associated documents and chunks
        await db.execute(delete(ChunkOllama).where(ChunkOllama.document_id.in_(
            select(Document.id).where(Document.collection_id == collection.id)
        )))
        await db.execute(delete(ChunkOpenAI).where(ChunkOpenAI.document_id.in_(
            select(Document.id).where(Document.collection_id == collection.id)
        )))
        await db.execute(delete(Document).where(Document.collection_id == collection.id))
        
        # Delete the collection
        await db.execute(delete(Collection).where(Collection.id == collection.id))
        
        await db.commit()
        return {"message": f"Collection '{collection_name}' and its documents deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
