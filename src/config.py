"""Configuration helpers for Prompt Library."""
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


def _config_dir() -> Path:
    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if appdata:
        base_dir = Path(appdata) / "PromptLibraryPro"
    else:
        base_dir = Path.home() / ".prompt_library_pro"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _config_path() -> Path:
    return _config_dir() / "config.json"


def _write_json_atomic(path: Path, data: Dict[str, Any]):
    tmp_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
    tmp_path = path.with_name(tmp_name)
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def load_config() -> Dict[str, Any]:
    path = _config_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_config(config: Dict[str, Any]):
    _write_json_atomic(_config_path(), config)


def get_data_dir() -> Optional[str]:
    config = load_config()
    data_dir = config.get("data_dir")
    if isinstance(data_dir, str) and data_dir.strip():
        return data_dir
    return None


def set_data_dir(path: str):
    config = load_config()
    config["data_dir"] = path
    save_config(config)


def get_sort_option(default: str = "Recently updated") -> str:
    config = load_config()
    value = config.get("sort_option")
    if isinstance(value, str) and value.strip():
        return value
    return default


def set_sort_option(option: str):
    config = load_config()
    config["sort_option"] = option
    save_config(config)


def get_theme(default: str = "light") -> str:
    config = load_config()
    value = config.get("theme")
    if isinstance(value, str) and value.strip():
        return value
    return default


def set_theme(theme: str):
    config = load_config()
    config["theme"] = theme
    save_config(config)


def get_ui_scale(default: str = "auto") -> str:
    """
    UI scaling preference.

    Stored as:
    - "auto" (recommended)
    - "1.25" (stringified float)
    """
    config = load_config()
    value = config.get("ui_scale")
    if isinstance(value, (int, float)):
        return str(float(value))
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def set_ui_scale(value: str):
    config = load_config()
    config["ui_scale"] = value
    save_config(config)
