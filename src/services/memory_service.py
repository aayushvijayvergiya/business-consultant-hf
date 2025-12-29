"""Memory service for conversation and context memory."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

try:
    from ..config import config
except ImportError:
    config = None


class MemoryService:
    """Service for managing conversation and context memory."""
    
    def __init__(self):
        """Initialize the memory service."""
        if config and hasattr(config, 'data_dir'):
            self.memory_dir = config.data_dir / "memory"
        else:
            self.memory_dir = Path(__file__).parent.parent.parent / "data" / "memory"
            self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from disk."""
        # Load sessions
        sessions_file = self.memory_dir / "sessions.json"
        if sessions_file.exists():
            try:
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
            except Exception as e:
                print(f"Error loading sessions: {e}")
                self.sessions = {}
        
        # Load user profiles
        profiles_file = self.memory_dir / "user_profiles.json"
        if profiles_file.exists():
            try:
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    self.user_profiles = json.load(f)
            except Exception as e:
                print(f"Error loading user profiles: {e}")
                self.user_profiles = {}
    
    def _save_memory(self):
        """Save memory to disk."""
        # Save sessions
        sessions_file = self.memory_dir / "sessions.json"
        try:
            with open(sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving sessions: {e}")
        
        # Save user profiles
        profiles_file = self.memory_dir / "user_profiles.json"
        try:
            with open(profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving user profiles: {e}")
    
    def create_session(self, session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new conversation session.
        
        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
            
        Returns:
            Session dictionary
        """
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": [],
            "context": {},
            "preferences": {}
        }
        
        self.sessions[session_id] = session
        self._save_memory()
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session dictionary or None if not found
        """
        return self.sessions.get(session_id)
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a message to a session.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.sessions[session_id]["messages"].append(message)
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
        self._save_memory()
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of messages
        """
        if session_id not in self.sessions:
            return []
        
        messages = self.sessions[session_id]["messages"]
        if limit:
            return messages[-limit:]
        return messages
    
    def update_context(self, session_id: str, context: Dict[str, Any]):
        """
        Update session context.
        
        Args:
            session_id: Session identifier
            context: Context dictionary to merge
        """
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        self.sessions[session_id]["context"].update(context)
        self.sessions[session_id]["updated_at"] = datetime.now().isoformat()
        self._save_memory()
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get session context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary
        """
        if session_id not in self.sessions:
            return {}
        return self.sessions[session_id].get("context", {})
    
    def create_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update a user profile.
        
        Args:
            user_id: User identifier
            profile_data: Profile data dictionary
            
        Returns:
            User profile dictionary
        """
        profile = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **profile_data
        }
        
        self.user_profiles[user_id] = profile
        self._save_memory()
        return profile
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile dictionary or None if not found
        """
        return self.user_profiles.get(user_id)
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """
        Update user preferences.
        
        Args:
            user_id: User identifier
            preferences: Preferences dictionary to merge
        """
        if user_id not in self.user_profiles:
            self.create_user_profile(user_id, {})
        
        if "preferences" not in self.user_profiles[user_id]:
            self.user_profiles[user_id]["preferences"] = {}
        
        self.user_profiles[user_id]["preferences"].update(preferences)
        self.user_profiles[user_id]["updated_at"] = datetime.now().isoformat()
        self._save_memory()
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            Preferences dictionary
        """
        if user_id not in self.user_profiles:
            return {}
        return self.user_profiles[user_id].get("preferences", {})
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False otherwise
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_memory()
            return True
        return False


# Global instance
_memory_service = None

def get_memory_service() -> MemoryService:
    """Get or create the global memory service instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service

