import requests
from typing import Optional, Dict, Any
import logging
from urllib.parse import urlparse
from pypdf import PdfReader
from io import BytesIO
import time

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize PDF processor with download settings.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of download retries
            retry_delay: Delay between retries in seconds
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
    def _validate_pdf_url(self, url: str) -> bool:
        """
        Validate if URL points to a PDF file.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is valid and points to PDF
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                logger.error(f"Invalid URL format: {url}")
                return False
            if not url.lower().endswith('.pdf'):
                logger.warning(f"URL does not end with .pdf: {url}")
            return True
        except Exception as e:
            logger.error(f"Error validating URL {url}: {str(e)}")
            return False
            
    def download_pdf(self, url: str) -> Optional[bytes]:
        """
        Download PDF with retries and timeout.
        
        Args:
            url: URL of PDF to download
            
        Returns:
            bytes: PDF content or None if download fails
        """
        if not self._validate_pdf_url(url):
            logger.error(f"Invalid PDF URL: {url}")
            return None
            
        logger.info(f"Starting PDF download from {url}")
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={'User-Agent': 'ResearchAssistant/1.0'}
                )
                response.raise_for_status()
                
                # Verify content type
                content_type = response.headers.get('content-type', '').lower()
                if 'application/pdf' not in content_type:
                    logger.error(f"Invalid content type for {url}: {content_type}")
                    return None
                    
                content_length = len(response.content)
                if content_length == 0:
                    logger.error(f"Empty PDF content from {url}")
                    return None
                    
                logger.info(f"Successfully downloaded PDF from {url} ({content_length} bytes)")
                return response.content
                
            except requests.RequestException as e:
                logger.warning(f"Download attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Waiting {self.retry_delay}s before retry {attempt + 2}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to download PDF from {url} after {self.max_retries} attempts")
                    return None
                    
        return None
        
    def extract_text(self, pdf_content: bytes) -> Optional[str]:
        """
        Extract text from PDF content.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            str: Extracted text or None if extraction fails
        """
        if not pdf_content:
            logger.error("No PDF content provided for text extraction")
            return None
            
        try:
            pdf_file = BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            if len(reader.pages) == 0:
                logger.error("PDF has no pages")
                return None
                
            logger.info(f"Starting text extraction from PDF with {len(reader.pages)} pages")
            text = ""
            for i, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                        logger.debug(f"Successfully extracted text from page {i} ({len(page_text)} characters)")
                    else:
                        logger.warning(f"No text extracted from page {i}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i}: {str(e)}")
                    continue
                    
            if not text:
                logger.error("No text extracted from any pages")
                return None
                
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Failed to read PDF: {str(e)}")
            return None
            
    def process_pdf(self, url: str) -> Dict[str, Any]:
        """
        Download and process PDF from URL.
        
        Args:
            url: URL of PDF to process
            
        Returns:
            Dict containing processing results and metadata
        """
        result = {
            "success": False,
            "url": url,
            "text": None,
            "error": None
        }
        
        pdf_content = self.download_pdf(url)
        if not pdf_content:
            result["error"] = "Failed to download PDF"
            return result
            
        text = self.extract_text(pdf_content)
        if not text:
            result["error"] = "Failed to extract text from PDF"
            return result
            
        result["success"] = True
        result["text"] = text
        return result 