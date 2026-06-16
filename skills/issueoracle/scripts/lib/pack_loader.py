from __future__ import annotations

from pathlib import Path
from typing import Any

from lib import schema

try:
    import yaml
except ImportError:
    yaml = None


def load_pack_dir(
    pack_path: Path,
) -> tuple[list[schema.Pattern], list[dict[str, Any]]]:
    patterns: list[schema.Pattern] = []
    errors: list[dict[str, Any]] = []

    if not pack_path.exists():
        return patterns, errors

    yaml_files = list(pack_path.rglob("*.yaml")) + list(pack_path.rglob("*.yml"))
    for yf in yaml_files:
        if "examples" in yf.parts:
            continue
        try:
            data = yaml.safe_load(yf.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append({"file": str(yf), "id": "?", "errors": [f"YAML parse error: {e}"]})
            continue

        if data is None:
            continue

        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = data.get("patterns", [data])
        else:
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            try:
                pattern = schema.Pattern(**entry)
                patterns.append(pattern)
            except Exception as e:
                pid = entry.get("id", "?")
                errors.append({"file": str(yf), "id": pid, "errors": [str(e)]})

    return patterns, errors
