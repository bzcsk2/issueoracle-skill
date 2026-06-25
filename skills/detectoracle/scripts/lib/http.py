"""Unified GitHub HTTP client with rate-limit handling, retry, caching."""

from __future__ import annotations

import contextlib
import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from lib import cache
from lib.version import USER_AGENT

GITHUB_API = "https://api.github.com"
_MAX_RETRIES = 3
_BASE_DELAY = 1.0
_DEFAULT_CACHE_TTL_SECONDS = 3600
_CACHE_TTL_SECONDS = _DEFAULT_CACHE_TTL_SECONDS
_OFFLINE_CACHE = False


def parse_cache_ttl_seconds(value: int | str) -> int:
    if isinstance(value, int):
        seconds = value
    else:
        text = value.strip().lower()
        if text.isdigit():
            seconds = int(text)
        else:
            unit = text[-1:] if text else ""
            number = text[:-1]
            multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            if unit not in multipliers or not number.isdigit():
                raise ValueError(f"Invalid cache TTL: {value!r}")
            seconds = int(number) * multipliers[unit]
    if seconds < 1:
        raise ValueError("Cache TTL must be positive")
    return seconds


def configure_cache(
    *,
    offline_cache: bool = False,
    cache_ttl_seconds: int | str = _DEFAULT_CACHE_TTL_SECONDS,
) -> None:
    global _CACHE_TTL_SECONDS, _OFFLINE_CACHE
    _OFFLINE_CACHE = offline_cache
    _CACHE_TTL_SECONDS = parse_cache_ttl_seconds(cache_ttl_seconds)


def _headers(token: str | None, etag: str = "") -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    if etag:
        h["If-None-Match"] = etag
    return h


def get_json(
    path: str,
    token: str | None = None,
    params: dict | None = None,
    use_cache: bool = True,
    cache_ttl: int | str | None = None,
) -> tuple[Any, dict[str, str | int]]:
    url = f"{GITHUB_API}{path}"
    if params:
        qs = urllib.parse.urlencode(params)
        url = f"{url}?{qs}"

    if use_cache:
        cached = cache.get("GET", url)
        if cached:
            return cached.get("_data", cached), {"cached": True, "source": "cache"}
        if _OFFLINE_CACHE:
            raise urllib.error.URLError(f"Offline cache miss: {url}")
    elif _OFFLINE_CACHE:
        raise urllib.error.URLError(f"Offline cache disabled network access: {url}")

    etag = cache.get_etag("GET", url) if use_cache else ""
    last_err: Exception | None = None
    rate_info: dict[str, str | int] = {}
    ttl_seconds = _CACHE_TTL_SECONDS if cache_ttl is None else parse_cache_ttl_seconds(cache_ttl)

    for attempt in range(_MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=_headers(token, etag))
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                encoding = resp.headers.get("Content-Encoding", "")
                if encoding == "gzip":
                    body = gzip.decompress(body)

                data: Any = json.loads(body.decode("utf-8"))

                rate_info = {
                    "remaining": resp.headers.get("X-RateLimit-Remaining", "?"),
                    "limit": resp.headers.get("X-RateLimit-Limit", "?"),
                    "reset": resp.headers.get("X-RateLimit-Reset", "?"),
                }

                if use_cache and resp.status == 200:
                    etag_val = resp.headers.get("ETag", "")
                    cache_payload = {"_data": data, "_etag": etag_val}
                    cache.set("GET", url, cache_payload, ttl_seconds=ttl_seconds)

                return data, rate_info

        except urllib.error.HTTPError as e:
            last_err = e
            body = e.read()
            if e.headers.get("Content-Encoding", "") == "gzip":
                body = gzip.decompress(body)
            with contextlib.suppress(Exception):
                json.loads(body.decode("utf-8"))

            rate_info = {
                "remaining": e.headers.get("X-RateLimit-Remaining", "?"),
                "limit": e.headers.get("X-RateLimit-Limit", "?"),
                "reset": e.headers.get("X-RateLimit-Reset", "?"),
            }

            if e.code == 304:
                cached = cache.get("GET", url)
                if cached:
                    return cached.get("_data", cached), {"cached": True, "source": "not-modified"}
                break

            if e.code in (403, 429):
                retry_after = _parse_retry_after(e.headers.get("Retry-After", ""))
                delay = retry_after or _BASE_DELAY * 2**attempt
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(min(delay, 60))
                    continue
            elif e.code >= 500 and attempt < _MAX_RETRIES - 1:
                time.sleep(_BASE_DELAY * (2**attempt))
                continue
            break

    raise last_err or urllib.error.URLError("Request failed after retries")


def _parse_retry_after(val: str) -> float | None:
    try:
        return float(val)
    except ValueError:
        return None
