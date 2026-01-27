"""JSON-based storage for prompts."""
import json
import os
import sys
import uuid
from pathlib import Path
from typing import List

from .models import Prompt, Category


class Storage:
    """Handles persistence of prompts to JSON file."""

    BACKUP_COUNT = 5
    HISTORY_LIMIT = 10

    def __init__(self, data_dir: str = None):
        """Initialize storage with optional custom data directory."""
        if data_dir is None:
            self.data_dir = self._default_data_dir()
        else:
            self.data_dir = Path(data_dir)
        
        self.prompts_file = self.data_dir / "prompts.json"
        self._restored_from_backup = False
        self._ensure_data_dir()

    @staticmethod
    def _default_data_dir() -> Path:
        """
        Pick a safe default storage directory.

        - When packaged (PyInstaller / frozen): store in the user's AppData by default,
          with an optional "portable mode" if a marker file exists next to the exe.
        - When running from source: keep using the repo's ./data folder if present
          (to avoid surprising developers), otherwise fall back to AppData.
        """
        # Packaged app: prefer per-user AppData (Program Files etc. may be read-only).
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).resolve().parent
            if (exe_dir / "PROMPTLIB_PORTABLE").exists() or (exe_dir / "portable.txt").exists():
                return exe_dir / "data"
            return Storage._user_data_dir()

        # Source/dev: use repo-local data/ if it exists.
        repo_data = Path(__file__).resolve().parent.parent / "data"
        if repo_data.exists():
            return repo_data

        return Storage._user_data_dir()

    @staticmethod
    def _user_data_dir() -> Path:
        """OS-appropriate per-user data directory (Windows-friendly)."""
        appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if appdata:
            return Path(appdata) / "PromptLibraryPro"
        return Path.home() / ".prompt_library_pro"

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.prompts_file.exists():
            self._save_raw([])

    def _backup_path(self, index: int) -> Path:
        """Return the backup path for the given index."""
        return self.prompts_file.with_suffix(self.prompts_file.suffix + f".bak{index}")

    def _rotate_backups(self):
        """Rotate backups (.bak1 .. .bakN)."""
        for i in range(self.BACKUP_COUNT, 1, -1):
            src = self._backup_path(i - 1)
            dst = self._backup_path(i)
            if src.exists():
                os.replace(src, dst)

        if self.prompts_file.exists():
            os.replace(self.prompts_file, self._backup_path(1))

    def _write_json_atomic(self, path: Path, data: List[dict], rotate_backups: bool = False):
        """Write JSON atomically to the given path."""
        tmp_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
        tmp_path = path.with_name(tmp_name)
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            if rotate_backups:
                self._rotate_backups()
            os.replace(tmp_path, path)
        except Exception:
            if rotate_backups and not path.exists():
                backup = self._backup_path(1)
                if backup.exists():
                    try:
                        os.replace(backup, path)
                    except OSError:
                        pass
            raise
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def _save_raw(self, data: List[dict]):
        """Save raw data to JSON file with backups and atomic replace."""
        self._write_json_atomic(self.prompts_file, data, rotate_backups=True)

    def _read_json(self, path: Path) -> List[dict]:
        """Read JSON data from disk."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _validate_prompt_item(self, item: dict, index: int):
        """Validate a single prompt item."""
        if not isinstance(item, dict):
            raise ValueError(f"Item {index} is not an object.")

        if "name" not in item or not isinstance(item.get("name"), str):
            raise ValueError(f"Item {index} is missing a 'name' string.")

        if "content" not in item or not isinstance(item.get("content"), str):
            raise ValueError(f"Item {index} is missing a 'content' string.")

        if "category" in item:
            category = item.get("category")
            valid_categories = {c.value for c in Category}
            if not isinstance(category, str) or category not in valid_categories:
                raise ValueError(
                    f"Item {index} has invalid 'category'. "
                    f"Expected one of: {', '.join(sorted(valid_categories))}."
                )

        if "tags" in item:
            tags = item.get("tags")
            if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
                raise ValueError(f"Item {index} has invalid 'tags' list (strings only).")

        if "sensitive" in item and not isinstance(item.get("sensitive"), bool):
            raise ValueError(f"Item {index} has invalid 'sensitive' (boolean expected).")

        if "pinned" in item and not isinstance(item.get("pinned"), bool):
            raise ValueError(f"Item {index} has invalid 'pinned' (boolean expected).")

        if "history" in item:
            history = item.get("history")
            if not isinstance(history, list):
                raise ValueError(f"Item {index} has invalid 'history' (list expected).")
            for h_idx, entry in enumerate(history, start=1):
                if not isinstance(entry, dict):
                    raise ValueError(
                        f"Item {index} has invalid 'history' entry {h_idx} (object expected)."
                    )

        for field_name in ("id", "created_at", "updated_at"):
            if field_name in item and not isinstance(item.get(field_name), str):
                raise ValueError(f"Item {index} has invalid '{field_name}' (string expected).")

    def _validate_prompt_list(self, data: List[dict]):
        """Validate the prompt list structure."""
        if not isinstance(data, list):
            raise ValueError("Top-level JSON must be a list of prompt objects.")
        for idx, item in enumerate(data, start=1):
            self._validate_prompt_item(item, idx)

    def _restore_from_backup(self) -> bool:
        """Restore prompts from the newest valid backup."""
        for i in range(1, self.BACKUP_COUNT + 1):
            backup = self._backup_path(i)
            if not backup.exists():
                continue
            try:
                data = self._read_json(backup)
                self._validate_prompt_list(data)
            except (json.JSONDecodeError, ValueError, OSError):
                continue

            # Restore without rotating backups to preserve history.
            self._write_json_atomic(self.prompts_file, data)
            self._restored_from_backup = True
            return True

        return False

    def consume_restore_flag(self) -> bool:
        """Return True if a restore just happened, and reset the flag."""
        if self._restored_from_backup:
            self._restored_from_backup = False
            return True
        return False

    def _load_raw(self) -> List[dict]:
        """Load raw data from JSON file."""
        try:
            data = self._read_json(self.prompts_file)
            self._validate_prompt_list(data)
            return data
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            if self._restore_from_backup():
                try:
                    data = self._read_json(self.prompts_file)
                    self._validate_prompt_list(data)
                    return data
                except (json.JSONDecodeError, ValueError, OSError):
                    pass
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
                history = p.history if isinstance(p.history, list) else []
                if self._should_add_version(p, prompt):
                    history.insert(0, self._snapshot_prompt(p))
                    history = history[: self.HISTORY_LIMIT]
                prompt.history = history
                prompt.update()
                prompts[i] = prompt
                self.save_prompts(prompts)
                return True
        return False

    def _should_add_version(self, existing: Prompt, updated: Prompt) -> bool:
        if existing.name != updated.name:
            return True
        if existing.content != updated.content:
            return True
        if existing.category != updated.category:
            return True
        if existing.tags != updated.tags:
            return True
        if existing.sensitive != updated.sensitive:
            return True
        if existing.pinned != updated.pinned:
            return True
        return False

    def _snapshot_prompt(self, prompt: Prompt) -> dict:
        return {
            "name": prompt.name,
            "content": prompt.content,
            "category": prompt.category.value,
            "tags": list(prompt.tags),
            "sensitive": bool(prompt.sensitive),
            "pinned": bool(prompt.pinned),
            "saved_at": prompt.updated_at,
        }

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt by ID."""
        prompts = self.load_prompts()
        original_len = len(prompts)
        prompts = [p for p in prompts if p.id != prompt_id]
        if len(prompts) < original_len:
            self.save_prompts(prompts)
            return True
        return False

    def delete_prompts(self, prompt_ids: List[str]) -> int:
        """Delete multiple prompts by ID. Returns count deleted."""
        if not prompt_ids:
            return 0
        prompts = self.load_prompts()
        id_set = set(prompt_ids)
        remaining = [p for p in prompts if p.id not in id_set]
        deleted = len(prompts) - len(remaining)
        if deleted:
            self.save_prompts(remaining)
        return deleted

    def export_to_file(self, filepath: str):
        """Export all prompts to a JSON file."""
        prompts = self.load_prompts()
        self.export_prompts_to_file(prompts, filepath)

    def export_prompts_to_file(self, prompts: List[Prompt], filepath: str):
        """Export provided prompts to a JSON file."""
        data = [p.to_dict() for p in prompts]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_from_file(self, filepath: str) -> int:
        """Import prompts from a JSON file. Returns count of imported prompts."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc.msg}") from exc

        self._validate_prompt_list(data)
        
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
