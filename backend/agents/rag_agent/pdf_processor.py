import logging
from typing import List, Dict
import os

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Process PDF files and extract text in chunks
    Uses PyPDF2 for PDF parsing
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Args:
            chunk_size: Number of words per chunk
            chunk_overlap: Number of overlapping words between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from PDF and split into chunks
        
        Returns:
            List of dicts with 'text' and 'metadata' keys
        """
        try:
            import PyPDF2
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF processing. "
                "Install it with: pip install PyPDF2 --break-system-packages"
            )

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        chunks = []
        filename = os.path.basename(pdf_path)

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)

                logger.info(f"📄 Processing {filename} ({total_pages} pages)")

                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()

                    if text.strip():
                        # Split page text into chunks
                        page_chunks = self._split_text(text)

                        for chunk_text in page_chunks:
                            chunks.append({
                                'text': chunk_text,
                                'metadata': {
                                    'source': filename,
                                    'page': page_num + 1,
                                    'total_pages': total_pages
                                }
                            })

                logger.info(f"✅ Extracted {len(chunks)} chunks from {filename}")
                return chunks

        except Exception as e:
            logger.error(f"❌ Error processing {filename}: {e}")
            raise

    def _split_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Full text to split
            
        Returns:
            List of text chunks
        """
        # Clean text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())  # Remove extra whitespace

        # Split into words
        words = text.split()

        if len(words) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)

            # Move start position with overlap
            start += self.chunk_size - self.chunk_overlap

        return chunks

    def extract_metadata(self, pdf_path: str) -> Dict:
        """Extract PDF metadata (title, author, etc.)"""
        try:
            import PyPDF2
        except ImportError:
            return {}

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata

                if metadata:
                    return {
                        'title': metadata.get('/Title', ''),
                        'author': metadata.get('/Author', ''),
                        'subject': metadata.get('/Subject', ''),
                        'creator': metadata.get('/Creator', ''),
                    }
        except:
            pass

        return {}