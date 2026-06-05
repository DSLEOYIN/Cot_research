"""Load editable prompt templates from JSON files."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


PROMPT_DIR = Path(__file__).resolve().parent / "prompts"


@lru_cache(maxsize=128)
def load_prompt(name: str) -> dict[str, Any] | None:
    path = PROMPT_DIR / f"{name}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def list_prompt_names() -> list[str]:
    if not PROMPT_DIR.exists():
        return []
    return sorted(path.stem for path in PROMPT_DIR.glob("*.json"))


def render_prompt(name: str, values: dict[str, Any]) -> str | None:
    prompt = load_prompt(name)
    if not prompt:
        return None

    parts = []
    for key in ("system_prompt", "user_prompt", "output_contract"):
        text = prompt.get(key)
        if text:
            parts.append(str(text))
    return render_template("\n\n".join(parts), values)


def render_template(template: str, values: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        value = values.get(key, "")
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2, default=str)
        return str(value)

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", replace, template)
