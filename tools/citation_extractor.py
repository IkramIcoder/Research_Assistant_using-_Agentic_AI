import re
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CitationExtractor:
    def __init__(self):
        """Initialize citation extractor with common patterns."""
        # Common citation patterns
        self.patterns = [
            # Numerical citations with optional text
            r'\[(\d+)\](?:\s*[A-Za-z\s\-\.\']+)?',  # [1] or [1] Author et al.
            r'\[(\d+(?:,\s*\d+)*)\]',  # [1,2,3] or [1, 2, 3]
            r'\[(?:\d+)(?:\-\d+)*\]',  # [1-3] or [1-3,4-6]
            r'\((\d+)\)',  # (1) or (1,2,3)
            r'\((\d+(?:,\s*\d+)*)\)',  # (1,2,3) or (1, 2, 3)
            
            # Author et al. (Year) format
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+et\s+al\.\s*\((\d{4})\)',
            r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+et\s+al\.\s*,\s*(\d{4})\)',
            
            # Single author (Year) format
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\((\d{4})\)',
            r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,\s*(\d{4})\)',
            
            # Two authors format
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+and\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\((\d{4})\)',
            r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+and\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(\d{4})\)',
            
            # Numerical citations
            r'\[([A-Za-z]+\d{2}(?:[a-z])?)\]',  # [Smi20], [Smi20a], etc.
            
            # More flexible author patterns
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+et\s+al\.\s*\((\d{4}(?:[a-z])?)\)',  # Allows for year with letter
            r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+et\s+al\.\s*,\s*(\d{4}(?:[a-z])?)\)',
            
            # Multiple authors with commas
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*\s+et\s+al\.\s*\((\d{4})\)',
            r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*\s+et\s+al\.\s*,\s*(\d{4})\)',
            
            # Citations with page numbers
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\((\d{4}),\s*p\.\s*\d+\)',
            r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,\s*(\d{4}),\s*p\.\s*\d+\)',
            
            # Citations with volume numbers
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\((\d{4}),\s*vol\.\s*\d+\)',
            r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,\s*(\d{4}),\s*vol\.\s*\d+\)'
        ]
        
    def _validate_year(self, year: str) -> bool:
        """
        Validate if year is reasonable.
        
        Args:
            year: Year string to validate
            
        Returns:
            bool: True if year is valid
        """
        try:
            # Remove any letter suffix (e.g., '2020a')
            year = re.sub(r'[a-z]$', '', year)
            year_int = int(year)
            current_year = datetime.now().year
            return 1800 <= year_int <= current_year + 1
        except ValueError:
            return False
            
    def _validate_author(self, author: str) -> bool:
        """
        Validate if author name is reasonable.
        
        Args:
            author: Author name to validate
            
        Returns:
            bool: True if author name is valid
        """
        # More flexible author name validation
        return (
            len(author.split()) >= 1 and
            bool(re.match(r'^[A-Za-z\s\-\.\']+$', author)) and
            len(author) >= 2  # At least 2 characters
        )
        
    def extract_citations(self, text: str) -> List[Dict[str, str]]:
        """
        Extract citations from text with context.
        
        Args:
            text: Text to extract citations from
            
        Returns:
            List of dictionaries containing citation details
        """
        if not text:
            logger.error("Empty text provided for citation extraction")
            return []
            
        citations = []
        seen_citations = set()
        
        # Try to find references section
        references_match = re.search(r'(?:References|Bibliography|Works Cited)\s*\n+(.*?)(?:\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)
        references_text = references_match.group(1) if references_match else ""
        
        # Process both main text and references
        texts_to_process = [(text, "inline"), (references_text, "reference")]
        
        for current_text, citation_type in texts_to_process:
            for pattern in self.patterns:
                matches = re.finditer(pattern, current_text)
                for match in matches:
                    try:
                        if '[' in pattern or '(' in pattern and any(c.isdigit() for c in match.group(0)):  # Handle numerical citations
                            citation_text = match.group(0)  # Get the full match for numerical citations
                            numbers = re.findall(r'\d+', citation_text)
                            if not numbers:
                                continue
                                
                            # Handle each number in the citation
                            for num in numbers:
                                citation = {
                                    "citation_text": citation_text,
                                    "number": num,
                                    "type": "numerical",
                                    "citation_type": citation_type,
                                    "context": current_text[max(0, match.start() - 50):min(len(current_text), match.end() + 50)].strip()
                                }
                                citation_key = f"{citation_type}_{citation_text}_{num}"
                                if citation_key not in seen_citations:
                                    citations.append(citation)
                                    seen_citations.add(citation_key)
                                    
                        elif 'and' in pattern:  # Handle two-author citations
                            author1 = match.group(1).strip()
                            author2 = match.group(2).strip()
                            year = match.group(3).strip()
                            if not (self._validate_author(author1) and self._validate_author(author2) and self._validate_year(year)):
                                continue
                            citation = {
                                "authors": [author1, author2],
                                "year": year,
                                "citation_type": citation_type,
                                "context": current_text[max(0, match.start() - 50):min(len(current_text), match.end() + 50)].strip()
                            }
                            citation_key = f"{citation_type}_{author1}_{author2}_{year}"
                            
                        else:  # Handle single author citations
                            author = match.group(1).strip()
                            year = match.group(2).strip()
                            if not (self._validate_author(author) and self._validate_year(year)):
                                continue
                            citation = {
                                "author": author,
                                "year": year,
                                "citation_type": citation_type,
                                "context": current_text[max(0, match.start() - 50):min(len(current_text), match.end() + 50)].strip()
                            }
                            citation_key = f"{citation_type}_{author}_{year}"
                            
                        if citation_key not in seen_citations:
                            citations.append(citation)
                            seen_citations.add(citation_key)
                            logger.debug(f"Found citation: {citation}")
                            
                    except Exception as e:
                        logger.warning(f"Error processing match {match.group(0)}: {str(e)}")
                        continue
                        
        logger.info(f"Found {len(citations)} unique citations")
        return citations
        
    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text and extract citations.
        
        Args:
            text: Text to process
            
        Returns:
            Dict containing processing results and metadata
        """
        result = {
            "success": False,
            "citations": [],
            "error": None
        }
        
        if not text:
            result["error"] = "Empty text provided"
            return result
            
        try:
            citations = self.extract_citations(text)
            result["success"] = True
            result["citations"] = citations
        except Exception as e:
            logger.error(f"Error during citation extraction: {str(e)}")
            result["error"] = str(e)
            
        return result 