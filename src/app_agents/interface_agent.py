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

from src.config import config
from src.services.memory_service import get_memory_service

load_dotenv(override=True)

# Import consultant manager
try:
    from src.app_agents.consultant_manager import ResearchManager
except ImportError as e:
    print(f"Warning: Could not import ResearchManager: {e}")
    ResearchManager = None


class InterfaceAgent:
    """Interface agent that refines user prompts and coordinates with consultant manager."""
    
    def __init__(self):
        """Initialize the interface agent."""
        # Use OpenRouter if available, otherwise fallback to OpenAI
        api_key = config.openrouter_api_key or config.openai_api_key
        base_url = config.openrouter_base_url if config.openrouter_api_key else None
        
        self.openai_client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        if ResearchManager is not None:
            self.consultant_manager = ResearchManager()
        else:
            self.consultant_manager = None
        
        self.memory_service = get_memory_service()
    
    def _refine_prompt(self, user_query: str, additional_context: Optional[str] = None) -> str:
        """
        Refine the user's prompt to make it more suitable for the consultant manager.
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
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error refining prompt: {e}")
            return query_text
    
    def _determine_if_clarification_needed(self, user_query: str, gathered_context: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Determine if clarification/context gathering is needed.
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
            if not result or "NO_CLARIFICATION_NEEDED" in result.upper():
                return False, None
            return True, result
        except Exception as e:
            print(f"Error determining clarification need: {e}")
            return True, default_clarification
    
    async def process_query(
        self, 
        user_query: str, 
        conversation_history: Optional[List] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Process a user query through the interface agent using MemoryService.
        """
        try:
            if self.consultant_manager is None:
                return "Consultant manager is not available."
            
            if session_id is None:
                session_id = f"session_{uuid.uuid4().hex[:8]}"
            
            # Use MemoryService for session state
            session = self.memory_service.get_session(session_id)
            if not session:
                session = self.memory_service.create_session(session_id)
            
            state = session.get("context", {})
            
            # Check if we're waiting for a response to a clarification question
            if state.get("waiting_for_clarification"):
                if state.get("current_clarification_question"):
                    context_entry = f"Q: {state['current_clarification_question']}\nA: {user_query}"
                    gathered_context = state.get("gathered_context_list", [])
                    gathered_context.append(context_entry)
                    state["gathered_context_list"] = gathered_context
                    state["waiting_for_clarification"] = False
                    state["current_clarification_question"] = None
                
                gathered_context_str = "\n".join(state.get("gathered_context_list", []))
                needs_clarification, clarification_question = self._determine_if_clarification_needed(
                    state.get("original_query", user_query),
                    gathered_context_str
                )
                
                if needs_clarification:
                    state["waiting_for_clarification"] = True
                    state["current_clarification_question"] = clarification_question
                    self.memory_service.update_context(session_id, state)
                    return clarification_question
                else:
                    state["ready_for_manager"] = True
            else:
                state["original_query"] = user_query
                state["gathered_context_list"] = []
                state["ready_for_manager"] = False
                
                needs_clarification, clarification_question = self._determine_if_clarification_needed(user_query)
                
                if needs_clarification:
                    state["waiting_for_clarification"] = True
                    state["current_clarification_question"] = clarification_question
                    self.memory_service.update_context(session_id, state)
                    return clarification_question
                else:
                    state["ready_for_manager"] = True
            
            if state.get("ready_for_manager"):
                gathered_context_str = "\n".join(state.get("gathered_context_list", []))
                refined_query = self._refine_prompt(state["original_query"], gathered_context_str)
                final_prompt = f"{refined_query}\n\nContext:\n{gathered_context_str}" if gathered_context_str else refined_query
                
                final_output = None
                async for update in self.consultant_manager.run(final_prompt):
                    final_output = update
                
                # Reset state after processing
                state["ready_for_manager"] = False
                state["waiting_for_clarification"] = False
                state["gathered_context_list"] = []
                self.memory_service.update_context(session_id, state)
                
                return final_output or "No output generated."
            
            self.memory_service.update_context(session_id, state)
            return "Processing..."
            
        except Exception as e:
            print(f"Error in interface agent: {e}")
            return f"Error: {str(e)}"


# Global instance
_interface_agent = None

def get_interface_agent() -> InterfaceAgent:
    """Get or create the global interface agent instance."""
    global _interface_agent
    if _interface_agent is None:
        _interface_agent = InterfaceAgent()
    return _interface_agent


async def run(query: str, history: Optional[List] = None, session_id: Optional[str] = None) -> str:
    """Main entry point for the interface agent."""
    agent = get_interface_agent()
    if session_id is None and history:
        session_id = f"session_{len(history)}"
    return await agent.process_query(query, history, session_id)
