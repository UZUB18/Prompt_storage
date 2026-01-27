"""Data models for the Prompt Library."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List
import uuid


class Category(str, Enum):
    """Prompt categories."""
    PERSONA = "Persona"
    SYSTEM_PROMPT = "System Prompt"
    TEMPLATE = "Template"
    OTHER = "Other"


@dataclass
class Prompt:
    """A single prompt entry."""
    name: str
    content: str
    category: Category = Category.OTHER
    tags: List[str] = field(default_factory=list)
    sensitive: bool = False
    pinned: bool = False
    history: List[dict] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "category": self.category.value,
            "tags": self.tags,
            "sensitive": self.sensitive,
            "pinned": self.pinned,
            "history": self.history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Prompt":
        """Create a Prompt from a dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            content=data["content"],
            category=Category(data.get("category", "Other")),
            tags=data.get("tags", []),
            sensitive=bool(data.get("sensitive", False)),
            pinned=bool(data.get("pinned", False)),
            history=data.get("history", []) if isinstance(data.get("history", []), list) else [],
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )

    def update(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now().isoformat()
