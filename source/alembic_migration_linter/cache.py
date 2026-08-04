from __future__ import annotations

import hashlib
import pickle
from pathlib import Path

_CACHE_DIR = Path.home() / ".cache" / "alembic-migration-linter"


def _get_cache_dir() -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


def get_cache_key(filepath: Path, dialect: str) -> str:
    """Return MD5 hash of file contents + dialect as cache key."""
    content = filepath.read_bytes() + dialect.encode()
    return hashlib.md5(content).hexdigest()  # noqa: S324


def get_cached_result(cache_key: str) -> object | None:
    """Retrieve a cached lint result."""
    cache_file = _get_cache_dir() / f"{cache_key}.pkl"
    if not cache_file.exists():
        return None
    with cache_file.open("rb") as f:
        return pickle.load(f)  # type: ignore[no-any-return]  # noqa: S301


def set_cached_result(cache_key: str, result: object) -> None:
    """Cache a lint result."""
    cache_file = _get_cache_dir() / f"{cache_key}.pkl"
    with cache_file.open("wb") as f:
        pickle.dump(result, f)
