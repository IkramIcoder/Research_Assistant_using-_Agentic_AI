from dotenv import load_dotenv
from agents.researcher_agent import create_research_agent
from utils.logger import configure_logger
from typing import Dict, Any, Optional
import os
import re
import time

load_dotenv()
logger = configure_logger()

def extract_first_pdf_url(results: Dict[str, Any]) -> Optional[str]:
    """
    Extract the first PDF URL from search results.
    
    Args:
        results: Dictionary containing search results
        
    Returns:
        str: First PDF URL found or None if no PDF URL found
    """
    if not results or not isinstance(results, dict):
        logger.error("Invalid results format")
        return None
        
    if 'results' not in results or not results['results']:
        logger.error("No results found in search response")
        return None
        
    for result in results['results']:
        if 'pdf_url' in result:
            return result['pdf_url']
        elif 'url' in result and result['url'].lower().endswith('.pdf'):
            return result['url']
            
    logger.warning("No PDF URL found in results")
    return None

def print_progress(message: str, delay: float = 0.5):
    """Print a progress message with animation."""
    for char in "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏":
        print(f"\r{char} {message}", end="", flush=True)
        time.sleep(delay)
    print("\r" + " " * (len(message) + 2) + "\r", end="", flush=True)

def get_user_input() -> tuple[str, int, str]:
    """
    Get user input for research parameters.
    
    Returns:
        tuple: (topic, num_papers, time_range)
    """
    print("\n" + "="*80)
    print("🔍 RESEARCH PARAMETERS")
    print("="*80)
    
    topic = input("\nEnter research topic: ").strip()
    while not topic:
        print("❌ Topic cannot be empty")
        topic = input("Enter research topic: ").strip()
    
    while True:
        try:
            num_papers = int(input("\nEnter number of papers to find (1-100): ").strip())
            if 1 <= num_papers <= 100:
                break
            print("❌ Please enter a number between 1 and 100")
        except ValueError:
            print("❌ Please enter a valid number")
    
    print("\nSelect time range:")
    print("1. Last year")
    print("2. Last 5 years")
    print("3. Last 10 years")
    print("4. All time")
    
    while True:
        try:
            choice = int(input("\nEnter your choice (1-4): ").strip())
            if 1 <= choice <= 4:
                break
            print("❌ Please enter a number between 1 and 4")
        except ValueError:
            print("❌ Please enter a valid number")
    
    time_ranges = {
        1: "last year",
        2: "last 5 years",
        3: "last 10 years",
        4: "all time"
    }
    
    print(f"DEBUG: User topic is '{topic}'")
    return topic, num_papers, time_ranges[choice]

def main():
    try:
        print_progress("Initializing research agent...")
        agent = create_research_agent()
        if not agent:
            logger.error("Failed to create research agent")
            return
            
        # Get user input for research parameters
        topic, num_papers, time_range = get_user_input()
        
        print("\n" + "="*80)
        print(f"🔍 SEARCHING PAPERS: {topic.upper()}")
        print("="*80)
        
        print_progress(f"Searching for papers about {topic}...")
        search_query = f"search papers about {topic}"
        print(f"DEBUG: Search query is '{search_query}'")
        search_result = agent.run(search_query, max_results=num_papers)
        results = search_result.get('results', [])
        print(f"\n📚 Searching for {num_papers} papers")
        
        # After retrieving search results
        for paper in results:
            print(f"DEBUG: Found paper '{paper['title']}'")
        
        # Download and summarize all found papers
        if results:
            # Limit the number of papers to process based on user input
            papers_to_process = results[:num_papers]
            print(f"\n📚 Processing {len(papers_to_process)} papers out of {len(results)} found")
            
            for idx, paper in enumerate(papers_to_process, 1):
                pdf_url = paper.get('pdf_url') or paper.get('url')
                if pdf_url:
                    print("\n" + "="*80)
                    print(f"📄 PAPER {idx} OF {num_papers}")
                    print("="*80)
                    print(f"\n📑 Reading paper: {pdf_url}")

                    print_progress(f"Downloading and analyzing paper {idx}...")
                    summary = agent.run(f"download and summarize this paper: {pdf_url}")

                    if summary.get('text'):
                        summary_text = summary['text']
                        sections = re.split(r'\n\s*\n', summary_text)
                        
                        # Define key sections to look for
                        key_sections = {
                            'abstract': ['abstract', 'summary'],
                            'introduction': ['introduction', 'background'],
                            'methods': ['methods', 'methodology', 'approach'],
                            'results': ['results', 'findings', 'analysis'],
                            'conclusion': ['conclusion', 'discussion', 'implications']
                        }
                        
                        # Process and display sections
                        print("\n" + "="*80)
                        print("📋 PAPER SUMMARY")
                        print("="*80)
                        
                        # Track which sections we've already processed
                        processed_sections = set()
                        current_section = None
                        
                        for section in sections:
                            section = section.strip()
                            if not section:
                                continue
                                
                            # Check if this is a key section
                            section_lower = section.lower()
                            section_found = False
                            
                            for section_type, keywords in key_sections.items():
                                if any(keyword in section_lower for keyword in keywords):
                                    # Only process if we haven't seen this section type before
                                    if section_type not in processed_sections:
                                        current_section = section_type.upper()
                                        processed_sections.add(section_type)
                                        print(f"\n📌 {current_section}")
                                        print("-"*40)
                                        # Skip the section header in the content
                                        content = section.split('\n', 1)[1] if '\n' in section else section
                                        print(content.strip())
                                        section_found = True
                                        break
                            
                            if not section_found:
                                # If not a key section, print under current section or as general content
                                if current_section:
                                    print(section)
                                else:
                                    print(f"\n📌 GENERAL CONTENT")
                                    print("-"*40)
                                    print(section)

                        # Extract and display citations
                        print("\n" + "="*80)
                        print("📑 CITATIONS")
                        print("="*80)

                        citations_result = agent.extract_citations(summary_text)
                        if citations_result.get('success', False):
                            citations = citations_result.get('citations', [])
                            if citations:
                                # Group citations by type
                                inline_citations = [c for c in citations if c.get('citation_type') == 'inline']
                                
                                # Group numerical citations
                                numerical_citations = {}
                                author_citations = []

                                for citation in inline_citations:
                                    if 'number' in citation:
                                        num = citation['number']
                                        if num not in numerical_citations:
                                            numerical_citations[num] = []
                                        numerical_citations[num].append(citation['citation_text'])
                                    else:
                                        author_citations.append(citation)

                                if numerical_citations:
                                    print("\n📌 Numerical Citations:")
                                    for num, citations_list in sorted(numerical_citations.items(), key=lambda x: int(x[0])):
                                        unique_citations = list(set(citations_list))
                                        print(f"[{num}] ({len(unique_citations)} occurrences)")

                                if author_citations:
                                    print("\n📌 Author Citations:")
                                    for i, citation in enumerate(author_citations, 1):
                                        if 'authors' in citation:
                                            print(f"{i}. {citation['authors'][0]} and {citation['authors'][1]} ({citation['year']})")
                                        else:
                                            print(f"{i}. {citation.get('author', '')} ({citation.get('year', '')})")
                            else:
                                print("\nNo citations found in the text.")
                        else:
                            print("\nError extracting citations:", citations_result.get('error', 'Unknown error'))

    except Exception as e:
        logger.error(f"Error in research workflow: {str(e)}", exc_info=True)
        print("\n❌ Error occurred during research workflow. Check logs for details.")

if __name__ == "__main__":
    main()