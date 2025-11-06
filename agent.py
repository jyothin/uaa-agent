# Standard library imports
import logging

# Tool imports

# Application-specific imports
from google.adk.agents.llm_agent import Agent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger.info("Logger initialized.")

# Goals
# 1. Get UAA server version
# 2. Install UAA server


root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Tells the current time and current weather in a specified city.',
    instruction='You are a helpful assistant that tells the current time and current weather in cities.',
    tools=[get_uaa_version, install_uaa],
)

def get_uaa_version() -> str:
    """Get the current UAA server version"""
    return ""


def install_uaa(repo_url, destination_path) -> str:
    """Install UAA server"""
    status = clone_repository(repo_url, destination_path)
    return status

from git import Repo
import os

def clone_repository(repo_url, destination_path):
    try:
        # Clone the repository
        Repo.clone_from(repo_url, destination_path)
        print(f"Repository cloned successfully to {destination_path}")
        return True
    except Exception as e:
        print(f"Error cloning repository: {str(e)}")
        return False

# Example usage
repo_url = "https://github.com/username/repository.git"
destination_path = os.path.join(os.getcwd(), "cloned_repo")
clone_repository(repo_url, destination_path)