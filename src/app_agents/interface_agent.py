"""Interface agent for business consultant - refines prompts and coordinates with consultant manager."""

import sys
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv
from openai import OpenAI

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(override=True)

# Import consultant manager
try:
    from src.app_agents.consultant_manager import ResearchManager
except ImportError as e:
    print(f"Warning: Could not import ResearchManager: {e}")
    ResearchManager = None

# Import config for OpenAI settings
try:
    from src.config import config
except ImportError:
    import os
    class Config:
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    config = Config()


class InterfaceAgent:
    """Interface agent that refines user prompts and coordinates with consultant manager."""
    
    def __init__(self):
        """Initialize the interface agent."""
        self.openai_client = OpenAI()
        if ResearchManager is not None:
            self.consultant_manager = ResearchManager()
        else:
            self.consultant_manager = None
        self.conversation_state: Dict[str, Any] = {}
    
    def _refine_prompt(self, user_query: str, additional_context: Optional[str] = None) -> str:
        """
        Refine the user's prompt to make it more suitable for the consultant manager.
        
        Args:
            user_query: The original user query
            additional_context: Optional additional context gathered from clarification questions
            
        Returns:
            Refined prompt string
        """
        system_prompt = """You are a helpful interface agent for a business consultant system.
Your role is to refine and clarify user queries to make them more suitable for deep business research and analysis.

When refining a query:
1. Make it more specific and actionable
2. Identify key business areas to explore
3. Ensure it's clear what kind of analysis or research is needed
4. Maintain the user's intent and core question
5. Incorporate any additional context provided

Return only the refined query, nothing else."""

        messages = [{"role": "system", "content": system_prompt}]
        
        query_text = user_query
        if additional_context:
            query_text = f"{user_query}\n\nAdditional context: {additional_context}"
        
        messages.append({"role": "user", "content": f"Refine this query: {query_text}"})
        
        try:
            response = self.openai_client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            refined_query = response.choices[0].message.content.strip()
            return refined_query
        except Exception as e:
            print(f"Error refining prompt: {e}")
            # Return original query if refinement fails
            return query_text
    
    def _determine_if_clarification_needed(self, user_query: str, gathered_context: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Determine if clarification/context gathering is needed before passing to consultant manager.
        
        Args:
            user_query: The user's query
            gathered_context: Any context already gathered from previous questions
            
        Returns:
            Tuple of (needs_clarification: bool, clarification_question: Optional[str])
        """
        default_clarification = "Thanks for reaching out! What business topic, industry, and goal should we focus on?"

        system_prompt = """You are a helpful interface agent for a business consultant system.
    Decide if the user message is a conversational greeting or a real business research/analysis request.

    - If it's a casual greeting or small talk: reply with a brief, warm acknowledgement and ask how you can help with their business question (max 25 words).
    - If it is a business query with a clear goal, context (industry/market), and task: respond with "NO_CLARIFICATION_NEEDED".
    - If it is vague/partial business intent: ask ONE focused, friendly question to get the missing business context (goal, industry/market, objective, timeline, constraints).

    Return only one of the above forms."""

        messages = [{"role": "system", "content": system_prompt}]
        
        query_text = user_query
        if gathered_context:
            query_text = f"Original query: {user_query}\n\nContext gathered so far: {gathered_context}"
        
        messages.append({"role": "user", "content": query_text})
        
        try:
            response = self.openai_client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )
            result = response.choices[0].message.content.strip()
            if not result:
                return True, default_clarification
            if "NO_CLARIFICATION_NEEDED" in result.upper():
                return False, None
            return True, result
        except Exception as e:
            print(f"Error determining clarification need: {e}")
            # Default to asking for clarification on error
            return True, default_clarification
    
    async def process_query(
        self, 
        user_query: str, 
        conversation_history: Optional[List] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Process a user query through the interface agent.
        
        This method:
        1. Determines if clarification/context gathering is needed
        2. Asks clarification questions if needed
        3. Once enough context is gathered, refines the prompt with all context
        4. Passes refined prompt + context to consultant manager
        5. Returns the final output
        
        Args:
            user_query: The user's input message
            conversation_history: Optional conversation history
            session_id: Optional session ID for state management
            
        Returns:
            Response string to display to the user (either clarification question or final output)
        """
        try:
            # Check if consultant manager is available
            if self.consultant_manager is None:
                return "Consultant manager is not available. Please check the configuration."
            
            # Generate or get session ID
            if session_id is None:
                session_id = f"session_{uuid.uuid4().hex[:8]}"
            
            # Initialize or get session state
            if session_id not in self.conversation_state:
                self.conversation_state[session_id] = {
                    "original_query": None,
                    "gathered_context": [],
                    "waiting_for_clarification": False,
                    "current_clarification_question": None,
                    "ready_for_manager": False
                }
            
            state = self.conversation_state[session_id]
            
            # Check if we're waiting for a response to a clarification question
            if state.get("waiting_for_clarification"):
                # User is responding to a clarification question
                # Add this response to gathered context
                if state.get("current_clarification_question"):
                    context_entry = f"Q: {state['current_clarification_question']}\nA: {user_query}"
                    state["gathered_context"].append(context_entry)
                    state["waiting_for_clarification"] = False
                    state["current_clarification_question"] = None
                
                # Check if we need more clarification
                gathered_context_str = "\n".join(state["gathered_context"])
                needs_clarification, clarification_question = self._determine_if_clarification_needed(
                    state.get("original_query", user_query),
                    gathered_context_str
                )
                
                if needs_clarification and clarification_question:
                    # Still need more context
                    state["waiting_for_clarification"] = True
                    state["current_clarification_question"] = clarification_question
                    return clarification_question
                else:
                    # We have enough context, proceed to consultant manager
                    state["ready_for_manager"] = True
            else:
                # This is a new query
                state["original_query"] = user_query
                state["gathered_context"] = []
                state["ready_for_manager"] = False
                
                # Check if clarification is needed
                needs_clarification, clarification_question = self._determine_if_clarification_needed(user_query)
                
                if needs_clarification and clarification_question:
                    # Need to gather more context first
                    state["waiting_for_clarification"] = True
                    state["current_clarification_question"] = clarification_question
                    return clarification_question
                else:
                    # No clarification needed, proceed directly to manager
                    state["ready_for_manager"] = True
            
            # If we're ready for the manager, process the query
            if state.get("ready_for_manager"):
                # Combine original query with all gathered context
                gathered_context_str = "\n".join(state["gathered_context"]) if state["gathered_context"] else None
                
                # Refine the prompt with all context
                refined_query = self._refine_prompt(
                    state.get("original_query", user_query),
                    gathered_context_str
                )
                
                # Create the final prompt to pass to consultant manager
                if gathered_context_str:
                    final_prompt = f"{refined_query}\n\nAdditional Context:\n{gathered_context_str}"
                else:
                    final_prompt = refined_query
                
                # Pass to consultant manager
                # The manager yields status updates, so we collect them
                status_updates = []
                final_output = None
                
                async for update in self.consultant_manager.run(final_prompt):
                    status_updates.append(update)
                    # The last update is typically the final report
                    final_output = update
                
                # Reset state after processing
                state["ready_for_manager"] = False
                state["waiting_for_clarification"] = False
                state["gathered_context"] = []
                state["current_clarification_question"] = None
                
                # Return the final output (usually the report)
                if final_output:
                    return final_output
                
                # If no final output, return the last status update
                if status_updates:
                    return status_updates[-1]
                
                return "Processing your query. Please wait..."
            
            # Should not reach here, but return a message just in case
            return "Processing your query. Please wait..."
            
        except Exception as e:
            print(f"Error in interface agent: {e}")
            import traceback
            traceback.print_exc()
            return f"I encountered an error while processing your query: {str(e)}. Please try again."


# Global instance
_interface_agent = None

def get_interface_agent() -> InterfaceAgent:
    """Get or create the global interface agent instance."""
    global _interface_agent
    if _interface_agent is None:
        _interface_agent = InterfaceAgent()
    return _interface_agent


async def run(query: str, history: Optional[List] = None, session_id: Optional[str] = None) -> str:
    """
    Main entry point for the interface agent.
    
    This function is called by the chat service.
    
    Args:
        query: User's input message
        history: Optional conversation history from Gradio
        session_id: Optional session ID (can be derived from history if needed)
        
    Returns:
        Response string to display
    """
    agent = get_interface_agent()
    
    # Generate session ID from history if not provided
    if session_id is None and history:
        # Use a simple hash of conversation length as session identifier
        session_id = f"session_{len(history)}"
    
    return await agent.process_query(query, history, session_id)
