from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from finance_ai_news.manifest import load_sources
from finance_ai_news.taxonomy import BOARD_ORDER, BOARD_DEFINITIONS, classify_and_tag_item

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "chapter1" / "output"
RECLASSIFIED_DIR = ROOT / "chapter2" / "output" / "reclassified"
MANIFEST_PATH = ROOT / "chapter1" / "day1_sources.json"


@dataclass
class UnifiedItem:
    id: str
    board: str
    section_id: str
    section_title: str
    section_subtitle: str
    bucket: str
    source_id: str
    source_name: str
    title: str
    snippet: str
    url: str
    published_at: str
    tags: Dict[str, List[str]]
    metadata: Dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "board": self.board,
            "section_id": self.section_id,
            "section_title": self.section_title,
            "section_subtitle": self.section_subtitle,
            "bucket": self.bucket,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "published_at": self.published_at,
            "tags": self.tags,
            "metadata": self.metadata,
        }


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_best_payload(filename: str) -> dict:
    reclassified_path = RECLASSIFIED_DIR / filename
    raw_path = OUTPUT_DIR / filename
    reclassified = _load_json(reclassified_path)
    raw = _load_json(raw_path)
    if not reclassified:
        return raw
    if not raw:
        return reclassified
    reclassified_time = reclassified.get("generated_at", "")
    raw_time = raw.get("generated_at", "")
    return reclassified if reclassified_time >= raw_time else raw


def _truncate(text: str, limit: int = 220) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _load_source_map() -> dict:
    return {source.id: source for source in load_sources(MANIFEST_PATH)}


def _build_unified_item(
    source_map: dict,
    result: dict,
    bucket: str,
    index: int,
    title: str,
    snippet: str,
    url: str,
    published_at: str,
    metadata: Dict[str, Any],
) -> UnifiedItem:
    source = source_map.get(result["source_id"])
    classification = classify_and_tag_item(
        source=source,
        title=title,
        snippet=snippet,
        url=url,
    )
    return UnifiedItem(
        id=f"{result['source_id']}:{bucket}:{index}",
        board=classification["board"],
        section_id=classification["section_id"],
        section_title=classification["section_title"],
        section_subtitle=classification["section_subtitle"],
        bucket=bucket,
        source_id=result["source_id"],
        source_name=result["source_name"],
        title=title,
        snippet=snippet,
        url=url,
        published_at=published_at,
        tags=classification["tags"],
        metadata={
            **metadata,
            "source_region": getattr(source, "region", ""),
            "source_channel": getattr(source, "channel", ""),
            "source_importance": getattr(source, "importance", ""),
            "section_description": classification["section_description"],
        },
    )


def _parse_x(payload: dict, source_map: dict) -> List[UnifiedItem]:
    items: List[UnifiedItem] = []
    for result in payload.get("results", []):
        for bucket in ["accepted_items", "review_items"]:
            normalized_bucket = "published" if bucket == "accepted_items" else "review"
            for index, item in enumerate(result.get(bucket, [])):
                content = item.get("content", "")
                title = _truncate(content.replace("\n", " "), 120)
                snippet = _truncate(content, 320)
                items.append(
                    _build_unified_item(
                        source_map=source_map,
                        result=result,
                        bucket=normalized_bucket,
                        index=index,
                        title=title,
                        snippet=snippet,
                        url=item.get("url", ""),
                        published_at=item.get("created_at", result.get("fetched_at", "")),
                        metadata={
                            "handle": result.get("handle", ""),
                            "filter_provider": result.get("filter_provider", ""),
                            "filter_reason": (item.get("filter_decision") or {}).get("reason", ""),
                            "finance_scope": item.get("source_finance_scope", ""),
                            "legacy_board": "fast_news_and_leaks",
                        },
                    )
                )
    return items


def _parse_generic(
    payload: dict,
    source_map: dict,
    default_board: str | None = None,
) -> List[UnifiedItem]:
    items: List[UnifiedItem] = []
    for result in payload.get("results", []):
        for bucket in ["accepted_items", "review_items"]:
            normalized_bucket = "published" if bucket == "accepted_items" else "review"
            for index, item in enumerate(result.get(bucket, [])):
                title = item.get("title") or item.get("content") or "Untitled"
                snippet = _truncate(
                    item.get("description")
                    or item.get("snippet")
                    or item.get("summary")
                    or item.get("subtitle")
                    or ""
                    or item.get("content")
                    or item.get("published")
                    or item.get("filter_decision", {}).get("reason", "")
                    or title,
                    320,
                )
                items.append(
                    _build_unified_item(
                        source_map=source_map,
                        result=result,
                        bucket=normalized_bucket,
                        index=index,
                        title=_truncate(title, 140),
                        snippet=snippet,
                        url=item.get("url", ""),
                        published_at=item.get("published", result.get("fetched_at", "")),
                        metadata={
                            "used_path": result.get("used_path", ""),
                            "filter_provider": result.get("filter_provider", ""),
                            "filter_reason": (item.get("filter_decision") or {}).get("reason", ""),
                            "finance_scope": item.get("source_finance_scope", ""),
                            "legacy_board": result.get("board") or default_board or "direct_rss",
                        },
                    )
                )
    return items


def _load_failures() -> List[dict]:
    failures = []
    for filename in [
        "x_latest.json",
        "web_latest.json",
        "youtube_latest.json",
        "bilibili_latest.json",
    ]:
        payload = _load_json(OUTPUT_DIR / filename)
        for item in payload.get("failures", []):
            failures.append({"file": filename, **item})
    return failures


def _resolve_provider_state(
    readiness_payload: dict,
    payloads: List[dict],
) -> tuple[str, bool]:
    provider = readiness_payload.get("provider", "unavailable")
    provider_ready = readiness_payload.get("provider_ready", False)

    observed_success_providers = []
    observed_success = False
    for payload in payloads:
        for result in payload.get("results", []):
            current = result.get("filter_provider", "")
            ready = result.get("filter_provider_ready")
            if current and not current.endswith("_error"):
                observed_success_providers.append(current)
            if ready or result.get("accepted_items") or result.get("rejected_items"):
                observed_success = True

    if observed_success_providers:
        provider = observed_success_providers[0]
    if observed_success:
        provider_ready = True
    return provider, provider_ready


def load_dashboard_state() -> dict:
    source_map = _load_source_map()
    x_payload = _load_best_payload("x_latest.json")
    web_payload = _load_best_payload("web_latest.json")
    youtube_payload = _load_best_payload("youtube_latest.json")
    bilibili_payload = _load_best_payload("bilibili_latest.json")
    readiness_payload = _load_json(ROOT / "chapter2" / "output" / "filter_readiness.json")
    provider, provider_ready = _resolve_provider_state(
        readiness_payload, [x_payload, web_payload, youtube_payload, bilibili_payload]
    )

    items = []
    items.extend(_parse_x(x_payload, source_map=source_map))
    items.extend(_parse_generic(web_payload, source_map=source_map))
    items.extend(_parse_generic(youtube_payload, source_map=source_map, default_board="long_form"))
    items.extend(_parse_generic(bilibili_payload, source_map=source_map, default_board="long_form"))
    items.sort(key=lambda item: item.published_at or "", reverse=True)

    boards = {board: [] for board in BOARD_ORDER}
    for item in items:
        boards.setdefault(item.board, []).append(item)

    board_payload = {}
    for board in BOARD_ORDER:
        board_items = boards.get(board, [])
        published_items = [item.to_dict() for item in board_items if item.bucket == "published"]
        review_items = [item.to_dict() for item in board_items if item.bucket == "review"]
        definition = BOARD_DEFINITIONS[board]
        board_payload[board] = {
            "meta": definition.to_dict(),
            "published": published_items,
            "review": review_items,
            "delivery": published_items,
        }

    total_delivery = sum(len(board["delivery"]) for board in board_payload.values())
    total_review = sum(len(board["review"]) for board in board_payload.values())

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "provider": provider,
        "provider_ready": provider_ready,
        "stats": {
            "total_delivery_items": total_delivery,
            "total_review_items": total_review,
            "total_failures": len(_load_failures()),
            "sources_live": sum(
                1
                for filename in [
                    OUTPUT_DIR / "x_latest.json",
                    OUTPUT_DIR / "web_latest.json",
                    OUTPUT_DIR / "youtube_latest.json",
                    OUTPUT_DIR / "bilibili_latest.json",
                ]
                if filename.exists()
            ),
        },
        "board_order": BOARD_ORDER,
        "board_meta": {board: definition.to_dict() for board, definition in BOARD_DEFINITIONS.items()},
        "boards": board_payload,
        "failures": _load_failures(),
    }
