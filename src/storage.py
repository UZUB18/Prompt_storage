"""JSON-based storage for prompts."""
import json
import os
from pathlib import Path
from typing import List

from .models import Prompt


class Storage:
    """Handles persistence of prompts to JSON file."""

    def __init__(self, data_dir: str = None):
        """Initialize storage with optional custom data directory."""
        if data_dir is None:
            # Default to 'data' folder next to the app
            self.data_dir = Path(__file__).parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
        self.prompts_file = self.data_dir / "prompts.json"
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.prompts_file.exists():
            self._save_raw([])

    def _save_raw(self, data: List[dict]):
        """Save raw data to JSON file."""
        with open(self.prompts_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_raw(self) -> List[dict]:
        """Load raw data from JSON file."""
        try:
            with open(self.prompts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def load_prompts(self) -> List[Prompt]:
        """Load all prompts from storage."""
        data = self._load_raw()
        return [Prompt.from_dict(item) for item in data]

    def save_prompts(self, prompts: List[Prompt]):
        """Save all prompts to storage."""
        data = [p.to_dict() for p in prompts]
        self._save_raw(data)

    def add_prompt(self, prompt: Prompt) -> Prompt:
        """Add a new prompt."""
        prompts = self.load_prompts()
        prompts.append(prompt)
        self.save_prompts(prompts)
        return prompt

    def update_prompt(self, prompt: Prompt) -> bool:
        """Update an existing prompt."""
        prompts = self.load_prompts()
        for i, p in enumerate(prompts):
            if p.id == prompt.id:
                prompt.update()
                prompts[i] = prompt
                self.save_prompts(prompts)
                return True
        return False

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt by ID."""
        prompts = self.load_prompts()
        original_len = len(prompts)
        prompts = [p for p in prompts if p.id != prompt_id]
        if len(prompts) < original_len:
            self.save_prompts(prompts)
            return True
        return False

    def export_to_file(self, filepath: str):
        """Export all prompts to a JSON file."""
        prompts = self.load_prompts()
        data = [p.to_dict() for p in prompts]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_from_file(self, filepath: str) -> int:
        """Import prompts from a JSON file. Returns count of imported prompts."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        existing = self.load_prompts()
        existing_ids = {p.id for p in existing}
        
        imported = 0
        for item in data:
            prompt = Prompt.from_dict(item)
            if prompt.id not in existing_ids:
                existing.append(prompt)
                imported += 1
        
        self.save_prompts(existing)
        return imported
