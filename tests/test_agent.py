# test_agent.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Change this import - the package name needs to match your folder name
from utils.logger import configure_logger  # Remove the absolute import attempt

from utils.logger import configure_logger
from agents.researcher_agent import create_research_agent
# from tools.web_search import WebSearchTool  # Not direct import

def test_agent_initialization():
    logger = configure_logger()
    agent = create_research_agent()
    assert agent is not None
    logger.info("Test passed!")
      
    