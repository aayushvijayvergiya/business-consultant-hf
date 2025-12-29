"""Knowledge base service for storing and retrieving business knowledge."""

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


class KnowledgeBase:
    """Knowledge base for storing and retrieving business knowledge."""
    
    def __init__(self):
        """Initialize the knowledge base."""
        if config and hasattr(config, 'knowledge_base_dir'):
            self.kb_dir = config.knowledge_base_dir
        else:
            self.kb_dir = Path(__file__).parent.parent.parent / "data" / "knowledge_base"
            self.kb_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.kb_dir / "index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load the knowledge base index."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading knowledge base index: {e}")
                return {}
        return {}
    
    def _save_index(self):
        """Save the knowledge base index."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving knowledge base index: {e}")
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for content."""
        return hashlib.md5(content.encode()).hexdigest()
    
    def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Store knowledge in the knowledge base.
        
        Args:
            content: The content to store
            metadata: Optional metadata dictionary
            category: Category for the knowledge
            tags: Optional list of tags
            
        Returns:
            ID of the stored knowledge
        """
        kb_id = self._generate_id(content)
        timestamp = datetime.now().isoformat()
        
        # Create knowledge entry
        entry = {
            "id": kb_id,
            "content": content,
            "category": category,
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": timestamp,
            "updated_at": timestamp,
            "access_count": 0
        }
        
        # Save to file
        kb_file = self.kb_dir / f"{kb_id}.json"
        try:
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving knowledge entry: {e}")
            return None
        
        # Update index
        self.index[kb_id] = {
            "category": category,
            "tags": tags or [],
            "created_at": timestamp,
            "file": str(kb_file)
        }
        self._save_index()
        
        return kb_id
    
    def retrieve(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve knowledge by ID.
        
        Args:
            kb_id: ID of the knowledge to retrieve
            
        Returns:
            Knowledge entry or None if not found
        """
        if kb_id not in self.index:
            return None
        
        kb_file = Path(self.index[kb_id]["file"])
        if not kb_file.exists():
            return None
        
        try:
            with open(kb_file, 'r', encoding='utf-8') as f:
                entry = json.load(f)
                # Update access count
                entry["access_count"] = entry.get("access_count", 0) + 1
                entry["updated_at"] = datetime.now().isoformat()
                
                # Save updated entry
                with open(kb_file, 'w', encoding='utf-8') as f:
                    json.dump(entry, f, indent=2, ensure_ascii=False)
                
                return entry
        except Exception as e:
            print(f"Error retrieving knowledge entry: {e}")
            return None
    
    def search(
        self,
        query: str = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.
        
        Args:
            query: Text query to search for
            category: Filter by category
            tags: Filter by tags
            limit: Maximum number of results
            
        Returns:
            List of matching knowledge entries
        """
        results = []
        
        for kb_id, index_entry in self.index.items():
            entry = self.retrieve(kb_id)
            if not entry:
                continue
            
            # Apply filters
            if category and entry.get("category") != category:
                continue
            
            if tags:
                entry_tags = entry.get("tags", [])
                if not any(tag in entry_tags for tag in tags):
                    continue
            
            if query:
                query_lower = query.lower()
                content = entry.get("content", "").lower()
                if query_lower not in content:
                    continue
            
            results.append(entry)
        
        # Sort by access count (most accessed first) or by date
        results.sort(key=lambda x: (x.get("access_count", 0), x.get("created_at", "")), reverse=True)
        
        return results[:limit]
    
    def get_categories(self) -> List[str]:
        """Get all categories in the knowledge base."""
        categories = set()
        for entry in self.index.values():
            if "category" in entry:
                categories.add(entry["category"])
        return sorted(list(categories))
    
    def get_tags(self) -> List[str]:
        """Get all tags in the knowledge base."""
        tags = set()
        for entry in self.index.values():
            if "tags" in entry:
                tags.update(entry["tags"])
        return sorted(list(tags))
    
    def delete(self, kb_id: str) -> bool:
        """
        Delete knowledge from the knowledge base.
        
        Args:
            kb_id: ID of the knowledge to delete
            
        Returns:
            True if deleted, False otherwise
        """
        if kb_id not in self.index:
            return False
        
        kb_file = Path(self.index[kb_id]["file"])
        if kb_file.exists():
            try:
                kb_file.unlink()
            except Exception as e:
                print(f"Error deleting knowledge file: {e}")
                return False
        
        del self.index[kb_id]
        self._save_index()
        return True


# Global instance
_knowledge_base = None

def get_knowledge_base() -> KnowledgeBase:
    """Get or create the global knowledge base instance."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base

