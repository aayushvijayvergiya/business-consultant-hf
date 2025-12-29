"""Chat service for handling conversations with the interface agent."""

import sys
from pathlib import Path

# Add the project root to the path to import app_agents
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app_agents import interface_agent_run


class ChatService:
    """Service for handling chat conversations with the interface agent."""
    
    def __init__(self):
        """Initialize the chat service."""
        pass
    
    async def chat(self, message: str, history=None) -> str:
        """
        Process a chat message by passing it to the interface agent and return the response.
        
        This method can be passed directly to Gradio's ChatInterface.
        Gradio supports both sync and async functions, so this will work seamlessly.
        
        Args:
            message: The user's input message
            history: Optional conversation history (passed to interface agent for context)
            
        Returns:
            The response message from the interface agent
        """
        try:
            # Call the async interface agent function with history for context
            response = await interface_agent_run(message, history=history)
            return response
        except Exception as e:
            print(f"Error in chat processing: {e}")
            return f"I'm sorry, I encountered an error while processing your message. Please try again."
