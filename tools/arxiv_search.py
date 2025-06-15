import arxiv
from typing import Dict, List, Optional, Set
import time
from datetime import datetime, timedelta, timezone
import logging
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

logger = logging.getLogger(__name__)

class ArxivSearch:
    def __init__(self, max_results: int = 10, rate_limit_delay: float = 3.0):
        """
        Initialize ArxivSearch with rate limiting.
        
        Args:
            max_results: Maximum number of results to return
            rate_limit_delay: Delay between requests in seconds
        """
        self.max_results = max_results
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = None
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
            
        self.stop_words = set(stopwords.words('english'))
        
    def _preprocess_query(self, query: str, max_terms: int = 10) -> str:
        """
        Preprocess and extract key terms from a long query.
        
        Args:
            query: Original search query
            max_terms: Maximum number of terms to include
            
        Returns:
            str: Processed query with key terms
        """
        if len(query) <= 200:  # If query is already short enough, return as is
            return query
            
        try:
            # Tokenize and convert to lowercase
            tokens = word_tokenize(query.lower())
            
            # Remove stopwords, punctuation, and short words
            filtered_tokens = [
                token for token in tokens 
                if token not in self.stop_words 
                and token.isalnum() 
                and len(token) > 2
            ]
            
            # Count term frequencies
            term_freq = Counter(filtered_tokens)
            
            # Get most common terms
            key_terms = [term for term, _ in term_freq.most_common(max_terms)]
            
            # Join terms with AND operator for more precise results
            processed_query = ' AND '.join(key_terms)
            
            logger.info(f"Processed query from {len(query)} chars to {len(processed_query)} chars")
            logger.debug(f"Extracted key terms: {key_terms}")
            
            return processed_query
            
        except Exception as e:
            logger.error(f"Error preprocessing query: {str(e)}")
            # Fallback to simple truncation if preprocessing fails
            return query[:200]
        
    def _check_rate_limit(self):
        """Enforce rate limiting between requests."""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
        
    def _format_pdf_url(self, arxiv_url: str) -> Optional[str]:
        """
        Format ArXiv URL to get the direct PDF link.
        
        Args:
            arxiv_url: ArXiv paper URL
            
        Returns:
            str: Direct PDF download URL or None if formatting fails
        """
        try:
            # Extract paper ID from URL
            paper_id = re.search(r'abs/([^/]+)$', arxiv_url)
            if not paper_id:
                logger.warning(f"Could not extract paper ID from URL: {arxiv_url}")
                return None
                
            paper_id = paper_id.group(1)
            
            # Validate paper ID format (YYMM.NNNNN or YYMM.NNNNNvN)
            if not re.match(r'^\d{4}\.\d{5}(?:v\d+)?$', paper_id):
                logger.warning(f"Invalid ArXiv paper ID format: {paper_id}")
                return None
                
            # Remove version number if present
            if 'v' in paper_id:
                paper_id = paper_id.split('v')[0]
                
            return f"https://arxiv.org/pdf/{paper_id}.pdf"
        except Exception as e:
            logger.error(f"Error formatting PDF URL: {str(e)}")
            return None
        
    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        days_back: int = 1095
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Search ArXiv for papers matching the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results (overrides init value)
            days_back: Only return papers from the last N days
            
        Returns:
            Dict containing list of paper results with metadata
        """
        if not query:
            logger.error("Empty search query")
            return {"results": []}
            
        try:
            print(f"DEBUG: ArxivSearch received query '{query}'")
            
            self._check_rate_limit()
            
            # Preprocess long queries
            if len(query) > 200:
                query = self._preprocess_query(query)
            
            # Calculate date filter with timezone awareness
            date_filter = datetime.now(timezone.utc) - timedelta(days=days_back)
            
            # Configure search
            search = arxiv.Search(
                query=query,
                max_results=max_results or self.max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            results = []
            for result in search.results():
                try:
                    # Ensure result.published is timezone aware
                    if result.published.tzinfo is None:
                        published = result.published.replace(tzinfo=timezone.utc)
                    else:
                        published = result.published
                        
                    # Skip papers older than date filter
                    if published < date_filter:
                        continue
                        
                    # Get direct PDF URL
                    pdf_url = self._format_pdf_url(result.entry_id)
                    if not pdf_url:
                        logger.warning(f"Skipping paper {result.entry_id} due to invalid PDF URL")
                        continue
                        
                    paper_data = {
                        "title": result.title,
                        "authors": [author.name for author in result.authors],
                        "summary": result.summary,
                        "published": published.isoformat(),
                        "pdf_url": pdf_url,
                        "doi": result.doi,
                        "arxiv_url": result.entry_id
                    }
                    results.append(paper_data)
                    
                    if len(results) >= (max_results or self.max_results):
                        break
                        
                except Exception as e:
                    logger.warning(f"Error processing search result: {str(e)}")
                    continue
                    
            return {"results": results}
            
        except arxiv.ArxivError as e:
            logger.error(f"ArXiv API error: {str(e)}")
            return {"results": [], "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during ArXiv search: {str(e)}")
            return {"results": [], "error": "An unexpected error occurred"} 