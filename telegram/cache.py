import os
import json
from typing import Set

# Simple persistent cache of NSFW unique IDs.
# This is a pragmatic disk-backed cache to accelerate repeated detections
# without hitting DB or re-running inference.
CACHE_DIR = os.environ.get("CACHE_DIR", os.path.join(os.getcwd(), "cache"))
CACHE_FILE = os.path.join(CACHE_DIR, "nsfw_unique_ids.json")

_nsrfw_unique_ids: Set[str] = set()

def _ensure_dir():
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
    except Exception:
        # If creation fails, we keep operating in-memory only
        pass

def _load():
    _ensure_dir()
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    _nsrfw_unique_ids.update(data)
    except Exception:
        # Corrupted or unreadable cache; ignore
        pass

def _persist():
    # Persist best-effort; ignore errors to not block the main flow
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(sorted(list(_nsrfw_unique_ids)), f)
    except Exception:
        pass

# Initialize cache at import
_load()

def is_nsfw_cached(unique_id: str) -> bool:
    if not unique_id:
        return False
    return unique_id in _nsrfw_unique_ids

def mark_nsfw_cached(unique_id: str) -> None:
    if not unique_id:
        return
    if unique_id not in _nsrfw_unique_ids:
        _nsrfw_unique_ids.add(unique_id)
        _persist()

def mark_safe_cached(unique_id: str) -> None:
    if not unique_id:
        return
    if unique_id in _nsrfw_unique_ids:
        _nsrfw_unique_ids.discard(unique_id)
        _persist()