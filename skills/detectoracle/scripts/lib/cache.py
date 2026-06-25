"""Simple disk cache with TTL and ETag support."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

from lib import env


def _cache_dir() -> Path:
    home = env.get_issueoracle_home()
    d = home / "cache" / "github"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _key(method: str, url: str) -> str:
    raw = f"{method}:{url}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get(method: str, url: str) -> dict | None:
    path = _cache_dir() / _key(method, url)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    ttl = data.get("_ttl")
    if ttl and datetime.datetime.now().timestamp() > ttl:
        path.unlink(missing_ok=True)
        return None
    return data


def set(method: str, url: str, payload: dict, ttl_seconds: int = 3600) -> None:
    payload["_ttl"] = datetime.datetime.now().timestamp() + ttl_seconds
    payload["_etag"] = payload.get("_etag", "")
    path = _cache_dir() / _key(method, url)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def get_etag(method: str, url: str) -> str:
    data = get(method, url)
    if data:
        return data.get("_etag", "")
    return ""


def clear(older_than_days: int = 7) -> int:
    count = 0
    threshold = datetime.datetime.now().timestamp() - older_than_days * 86400
    for p in _cache_dir().iterdir():
        if p.is_file() and p.stat().st_mtime < threshold:
            p.unlink()
            count += 1
    return count
