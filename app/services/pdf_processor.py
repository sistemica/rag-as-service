import PyPDF2
from typing import List, Tuple
from app.core.config import settings
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

def process_pdf(content: bytes) -> List[Tuple[str, int]]:
    """
    Process PDF content and return chunks with their page numbers.
    Returns: List of (chunk_text, page_number) tuples
    """
    try:
        reader = PyPDF2.PdfReader(BytesIO(content))
        chunks_with_pages = []
        
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            # Simple chunking by paragraphs - you might want to use a more sophisticated approach
            paragraphs = text.split('\n\n')
            for paragraph in paragraphs:
                if len(paragraph.strip()) > 0:
                    chunks_with_pages.append((paragraph.strip(), page_num))
        
        return chunks_with_pages
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise
