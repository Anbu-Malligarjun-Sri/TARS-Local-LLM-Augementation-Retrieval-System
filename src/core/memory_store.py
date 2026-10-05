"""
TARS Memory Store
Manages conversation history and context persistence.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field, asdict
import logging
from uuid import uuid4


logger = logging.getLogger("tars.memory")


@dataclass
class Message:
    """Represents a single message in conversation history."""
    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for LLM APIs."""
        return {"role": self.role, "content": self.content}


@dataclass
class Conversation:
    """Represents a conversation session."""
    id: str
    messages: list[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: dict | None = None) -> Message:
        """Add a message to the conversation."""
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        return msg
    
    def get_history(self, max_messages: int | None = None) -> list[dict]:
        """Get conversation history in LLM-compatible format."""
        messages = self.messages[-max_messages:] if max_messages else self.messages
        return [msg.to_dict() for msg in messages]
    
    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()


class MemoryStore:
    """
    Manages conversation memory with optional persistence.
    
    Features:
    - In-memory conversation storage
    - JSON file persistence
    - Conversation history limiting
    - Context window management
    """
    
    def __init__(
        self,
        persist_dir: str | Path | None = None,
        max_messages_per_conversation: int = 50,
        auto_save: bool = True
    ):
        self.persist_dir = Path(persist_dir) if persist_dir else None
        self.max_messages = max_messages_per_conversation
        self.auto_save = auto_save
        
        self.conversations: dict[str, Conversation] = {}
        self.active_conversation_id: str | None = None
        
        if self.persist_dir:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._load_conversations()
    
    def create_conversation(self, conversation_id: str | None = None) -> Conversation:
        """Create a new conversation."""
        if conversation_id is None:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        
        conversation = Conversation(id=conversation_id)
        self.conversations[conversation_id] = conversation
        self.active_conversation_id = conversation_id
        
        logger.info(f"Created new conversation: {conversation_id}")
        
        if self.auto_save:
            self._save_conversation(conversation)
        
        return conversation
    
    def get_conversation(self, conversation_id: str | None = None) -> Conversation | None:
        """Get a conversation by ID, or the active conversation."""
        conv_id = conversation_id or self.active_conversation_id
        if conv_id is None:
            return None
        return self.conversations.get(conv_id)
    
    def get_or_create_active(self) -> Conversation:
        """Get the active conversation or create a new one."""
        if self.active_conversation_id and self.active_conversation_id in self.conversations:
            return self.conversations[self.active_conversation_id]
        return self.create_conversation()
    
    def add_message(
        self,
        role: str,
        content: str,
        conversation_id: str | None = None,
        metadata: dict | None = None
    ) -> Message:
        """Add a message to a conversation."""
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            conversation = self.create_conversation(conversation_id)
        
        msg = conversation.add_message(role, content, metadata)
        
        # Trim if exceeds max messages
        if len(conversation.messages) > self.max_messages:
            conversation.messages = conversation.messages[-self.max_messages:]
        
        if self.auto_save:
            self._save_conversation(conversation)
        
        return msg
    
    def get_history(
        self,
        conversation_id: str | None = None,
        max_messages: int | None = None
    ) -> list[dict]:
        """Get conversation history in LLM-compatible format."""
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            return []
        return conversation.get_history(max_messages)
    
    def clear_conversation(self, conversation_id: str | None = None) -> None:
        """Clear a conversation's messages."""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.clear()
            if self.auto_save:
                self._save_conversation(conversation)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation entirely."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            
            if self.persist_dir:
                file_path = self.persist_dir / f"{conversation_id}.json"
                if file_path.exists():
                    file_path.unlink()
            
            if self.active_conversation_id == conversation_id:
                self.active_conversation_id = None
            
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        
        return False
    
    def list_conversations(self) -> list[dict[str, str]]:
        """List all conversations with their IDs and creation times."""
        return [
            {"id": conv.id, "created_at": conv.created_at, "message_count": len(conv.messages)}
            for conv in self.conversations.values()
        ]
    
    def _save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation to disk."""
        if self.persist_dir is None:
            return
        
        file_path = self.persist_dir / f"{conversation.id}.json"
        data = {
            "id": conversation.id,
            "created_at": conversation.created_at,
            "metadata": conversation.metadata,
            "messages": [asdict(msg) for msg in conversation.messages]
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_conversations(self) -> None:
        """Load conversations from disk."""
        if self.persist_dir is None:
            return
        
        for file_path in self.persist_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                conversation = Conversation(
                    id=data["id"],
                    created_at=data.get("created_at", datetime.now().isoformat()),
                    metadata=data.get("metadata", {})
                )
                
                for msg_data in data.get("messages", []):
                    conversation.messages.append(Message(
                        role=msg_data["role"],
                        content=msg_data["content"],
                        timestamp=msg_data.get("timestamp", datetime.now().isoformat()),
                        metadata=msg_data.get("metadata", {})
                    ))
                
                self.conversations[conversation.id] = conversation
                logger.debug(f"Loaded conversation: {conversation.id}")
            
            except Exception as e:
                logger.error(f"Error loading conversation {file_path}: {e}")


# Global memory store instance
_memory_store: MemoryStore | None = None


def get_memory_store(persist_dir: str | Path | None = None) -> MemoryStore:
    """Get or create the global memory store."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore(persist_dir=persist_dir)
    return _memory_store
