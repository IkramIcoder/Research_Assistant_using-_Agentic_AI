# agents/researcher_agent.py
from typing import Dict, Any, Optional
import logging
from tools.arxiv_search import ArxivSearch
from tools.pdf_processor import PDFProcessor
from tools.citation_extractor import CitationExtractor
import re

logger = logging.getLogger(__name__)

class ResearcherAgent:
    def __init__(
        self,
        max_search_results: int = 5,
        rate_limit_delay: float = 3.0,
        pdf_timeout: int = 30
    ):
        """
        Initialize researcher agent with tools and settings.
        
        Args:
            max_search_results: Maximum number of search results
            rate_limit_delay: Delay between API requests
            pdf_timeout: Timeout for PDF downloads
        """
        self.arxiv_search = ArxivSearch(
            max_results=max_search_results,
            rate_limit_delay=rate_limit_delay
        )
        self.pdf_processor = PDFProcessor(timeout=pdf_timeout)
        self.citation_extractor = CitationExtractor()
        
    def search_papers(self, query: str, max_results: int = None) -> Dict[str, Any]:
        """
        Search for papers matching the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Dict containing search results
        """
        try:
            return self.arxiv_search.search(query, max_results=max_results)
        except Exception as e:
            logger.error(f"Error during paper search: {str(e)}")
            return {"results": [], "error": str(e)}
            
    def process_paper(self, url: str) -> Dict[str, Any]:
        """
        Download and process a paper.
        
        Args:
            url: URL of paper to process
            
        Returns:
            Dict containing processing results
        """
        try:
            return self.pdf_processor.process_pdf(url)
        except Exception as e:
            logger.error(f"Error during paper processing: {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
            
    def extract_citations(self, text: str) -> Dict[str, Any]:
        """
        Extract citations from text.
        
        Args:
            text: Text to extract citations from
            
        Returns:
            Dict containing extracted citations
        """
        try:
            return self.citation_extractor.process_text(text)
        except Exception as e:
            logger.error(f"Error during citation extraction: {str(e)}")
            return {
                "success": False,
                "citations": [],
                "error": str(e)
            }
            
    def run(self, task: str, max_results: int = None) -> Dict[str, Any]:
        """
        Run a research task.
        
        Args:
            task: Task description
            max_results: Maximum number of results to return
            
        Returns:
            Dict containing task results
        """
        if not task or not isinstance(task, str):
            logger.error("Invalid task: must be a non-empty string")
            return {
                "success": False,
                "error": "Invalid task: must be a non-empty string"
            }
            
        try:
            task_lower = task.lower().strip()
            
            # Search task
            if "search" in task_lower and ("paper" in task_lower or "research" in task_lower):
                # Extract the actual topic from the task string
                # e.g., "search papers about quantum physics" -> "quantum physics"
                match = re.search(r"about (.+)", task_lower)
                if match:
                    query = match.group(1).strip()
                else:
                    # fallback: remove "search" and "papers" and use the rest
                    query = task_lower.replace("search", "").replace("papers", "").strip()
                logger.info(f"DEBUG: Agent is searching for '{query}'")
                logger.info(f"Executing search task with query: {query}")
                return self.search_papers(query, max_results=max_results)
                
            # Download and summarize task
            elif any(word in task_lower for word in ["download", "summarize", "read"]):
                # Extract URL from task
                url_start = task.find("http")
                if url_start == -1:
                    raise ValueError("No URL found in task")
                    
                # Find the end of the URL (first space or end of string)
                url_end = task.find(" ", url_start)
                if url_end == -1:
                    url_end = len(task)
                    
                url = task[url_start:url_end].rstrip(".,;")
                if not url:
                    raise ValueError("Invalid URL in task")
                    
                logger.info(f"Executing paper processing task for URL: {url}")
                return self.process_paper(url)
                
            # Citation extraction task
            elif "citation" in task_lower or "reference" in task_lower:
                # Extract text from task
                text_parts = task.split(":", 1)
                if len(text_parts) < 2:
                    raise ValueError("No text provided for citation extraction")
                    
                text = text_parts[1].strip()
                if not text:
                    raise ValueError("Empty text for citation extraction")
                    
                logger.info(f"Executing citation extraction task on text of length {len(text)}")
                return self.extract_citations(text)
                
            else:
                raise ValueError(f"Unknown task type: {task}")
                
        except ValueError as e:
            logger.error(f"Invalid task format: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error during task execution: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

def create_research_agent() -> Optional[ResearcherAgent]:
    """
    Create and return a configured researcher agent.
    
    Returns:
        ResearcherAgent instance or None if creation fails
    """
    try:
        return ResearcherAgent()
    except Exception as e:
        logger.error(f"Failed to create research agent: {str(e)}")
        return None