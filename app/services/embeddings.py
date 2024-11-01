import httpx
from app.core.config import settings, EmbeddingProvider
import logging
from typing import List, Union
import numpy as np

logger = logging.getLogger(__name__)

async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings for a list of texts using the configured embedding provider."""
    try:
        logger.debug(f"Getting embeddings for {len(texts)} texts")
        if settings.EMBEDDING_PROVIDER == EmbeddingProvider.OLLAMA:
            embeddings = await get_ollama_embeddings(texts)
        elif settings.EMBEDDING_PROVIDER == EmbeddingProvider.OPENAI:
            embeddings = await get_openai_embeddings(texts)
        else:
            raise ValueError(f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}")
        
        logger.debug(f"Embeddings generated. Type: {type(embeddings)}, Length: {len(embeddings)}")
        for i, embedding in enumerate(embeddings):
            logger.debug(f"Embedding {i}: Type: {type(embedding)}, Length: {len(embedding) if isinstance(embedding, (list, tuple)) else 'N/A'}")
        
        # Ensure all embeddings are lists of floats
        validated_embeddings = []
        for embedding in embeddings:
            if isinstance(embedding, (list, tuple)):
                validated_embedding = [float(x) for x in embedding]
            elif isinstance(embedding, str):
                try:
                    validated_embedding = [float(x) for x in eval(embedding)]
                except:
                    logger.warning(f"Failed to parse embedding string: {embedding[:100]}...")
                    validated_embedding = []
            else:
                logger.warning(f"Unexpected embedding type: {type(embedding)}")
                validated_embedding = []
            
            validated_embeddings.append(validated_embedding)
        
        logger.debug(f"Validated embeddings: {validated_embeddings[:2]}")  # Log first two embeddings
        return validated_embeddings
        
        # Ensure all embeddings are lists of floats
        validated_embeddings = []
        for embedding in embeddings:
            if isinstance(embedding, (list, tuple)):
                validated_embedding = [float(x) for x in embedding]
            elif isinstance(embedding, str):
                try:
                    validated_embedding = [float(x) for x in eval(embedding)]
                except:
                    logger.warning(f"Failed to parse embedding string: {embedding[:100]}...")
                    validated_embedding = []
            else:
                logger.warning(f"Unexpected embedding type: {type(embedding)}")
                validated_embedding = []
            
            validated_embeddings.append(validated_embedding)
        
        return validated_embeddings
    except Exception as e:
        logger.error(f"Error getting embeddings: {e}")
        raise

async def get_ollama_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings from Ollama API and adjust dimensions."""
    async with httpx.AsyncClient() as client:
        embeddings = []
        for text in texts:
            try:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                    json={"model": settings.EMBEDDING_MODEL, "prompt": text},
                    timeout=30.0
                )
                response.raise_for_status()
                embedding = response.json().get("embedding")
                
                if not isinstance(embedding, list):
                    logger.warning(f"Unexpected embedding type: {type(embedding)}. Expected list.")
                    embedding = [embedding] if isinstance(embedding, (int, float)) else []
                
                adjusted_embedding = adjust_embedding_dimension(embedding, settings.EMBEDDING_DIMENSION)
                validated_embedding = [float(x) for x in adjusted_embedding]
                
                if len(validated_embedding) != settings.EMBEDDING_DIMENSION:
                    logger.warning(f"Embedding dimension mismatch. Expected {settings.EMBEDDING_DIMENSION}, got {len(validated_embedding)}")
                    validated_embedding = validated_embedding[:settings.EMBEDDING_DIMENSION] + [0.0] * max(0, settings.EMBEDDING_DIMENSION - len(validated_embedding))
                
                embeddings.append(validated_embedding)
                logger.debug(f"Processed embedding: length={len(validated_embedding)}")
            except Exception as e:
                logger.error(f"Error processing embedding for text: {text[:50]}... Error: {str(e)}")
                embeddings.append([0.0] * settings.EMBEDDING_DIMENSION)  # Fallback to zero vector
        
        logger.debug(f"Generated {len(embeddings)} embeddings")
        return embeddings

def adjust_embedding_dimension(embedding: List[float], target_dim: int) -> List[float]:
    """Adjust the embedding dimension to match the target dimension."""
    current_dim = len(embedding)
    if current_dim == target_dim:
        return embedding
    elif current_dim < target_dim:
        return embedding + [0.0] * (target_dim - current_dim)
    else:
        return embedding[:target_dim]

def adjust_embedding_dimension(embedding: Union[List[float], float], target_dim: int) -> List[float]:
    """Adjust the embedding dimension to match the target dimension."""
    if not isinstance(embedding, list):
        embedding = [float(embedding)]  # Ensure it's a list, even if a single float
    current_dim = len(embedding)
    if current_dim == target_dim:
        return embedding
    elif current_dim < target_dim:
        return embedding + [0.0] * (target_dim - current_dim)
    else:
        # If we need to reduce dimensions, we'll use PCA
        embedding_array = np.array(embedding).reshape(1, -1)
        pca = np.linalg.svd(embedding_array, full_matrices=False)
        reduced_embedding = pca[0] @ np.diag(pca[1])[:, :target_dim]
        return reduced_embedding.flatten().tolist()

def adjust_embedding_dimension(embedding: Union[List[float], float], target_dim: int) -> List[float]:
    """Adjust the embedding dimension to match the target dimension."""
    if not isinstance(embedding, list):
        embedding = [float(embedding)]
    current_dim = len(embedding)
    if current_dim == target_dim:
        return embedding
    elif current_dim < target_dim:
        return embedding + [0.0] * (target_dim - current_dim)
    else:
        # If we need to reduce dimensions, we'll use PCA
        embedding_array = np.array(embedding).reshape(1, -1)
        pca = np.linalg.svd(embedding_array, full_matrices=False)
        reduced_embedding = pca[0] @ np.diag(pca[1])[:, :target_dim]
        return reduced_embedding.flatten().tolist()

async def get_openai_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings from OpenAI API."""
    # Implement OpenAI embedding logic here
    # For now, we'll raise a NotImplementedError
    raise NotImplementedError("OpenAI embeddings not yet implemented")
