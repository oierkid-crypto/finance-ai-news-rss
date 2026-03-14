from __future__ import annotations

import json
from pathlib import Path
from typing import List

from finance_ai_news.models import Source


def load_sources(manifest_path: Path) -> List[Source]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [Source.from_dict(item) for item in payload["sources"]]


def filter_day1_core(sources: List[Source]) -> List[Source]:
    return [source for source in sources if source.importance == "P0"]
