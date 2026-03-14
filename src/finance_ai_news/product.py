from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "chapter1" / "output"
RECLASSIFIED_DIR = ROOT / "chapter2" / "output" / "reclassified"


@dataclass
class UnifiedItem:
    id: str
    board: str
    bucket: str
    source_id: str
    source_name: str
    title: str
    snippet: str
    url: str
    published_at: str
    metadata: Dict[str, str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "board": self.board,
            "bucket": self.bucket,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "published_at": self.published_at,
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


def _parse_x(payload: dict) -> List[UnifiedItem]:
    items: List[UnifiedItem] = []
    for result in payload.get("results", []):
        for bucket in ["accepted_items", "review_items"]:
            normalized_bucket = "published" if bucket == "accepted_items" else "review"
            for index, item in enumerate(result.get(bucket, [])):
                content = item.get("content", "")
                title = _truncate(content.replace("\n", " "), 120)
                items.append(
                    UnifiedItem(
                        id=f"{result['source_id']}:{normalized_bucket}:{index}",
                        board="fast_news_and_leaks",
                        bucket=normalized_bucket,
                        source_id=result["source_id"],
                        source_name=result["source_name"],
                        title=title,
                        snippet=_truncate(content, 320),
                        url=item.get("url", ""),
                        published_at=item.get("created_at", result.get("fetched_at", "")),
                        metadata={
                            "handle": result.get("handle", ""),
                            "filter_provider": result.get("filter_provider", ""),
                            "filter_reason": (item.get("filter_decision") or {}).get("reason", ""),
                            "finance_scope": item.get("source_finance_scope", ""),
                        },
                    )
                )
    return items


def _parse_generic(payload: dict, default_board: str | None = None) -> List[UnifiedItem]:
    items: List[UnifiedItem] = []
    for result in payload.get("results", []):
        board = result.get("board") or default_board or "direct_rss"
        for bucket in ["accepted_items", "review_items"]:
            normalized_bucket = "published" if bucket == "accepted_items" else "review"
            for index, item in enumerate(result.get(bucket, [])):
                title = item.get("title") or item.get("content") or "Untitled"
                items.append(
                    UnifiedItem(
                        id=f"{result['source_id']}:{normalized_bucket}:{index}",
                        board=board,
                        bucket=normalized_bucket,
                        source_id=result["source_id"],
                        source_name=result["source_name"],
                        title=_truncate(title, 140),
                        snippet=_truncate(
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
                        ),
                        url=item.get("url", ""),
                        published_at=item.get("published", result.get("fetched_at", "")),
                        metadata={
                            "used_path": result.get("used_path", ""),
                            "filter_provider": result.get("filter_provider", ""),
                            "filter_reason": (item.get("filter_decision") or {}).get("reason", ""),
                            "finance_scope": item.get("source_finance_scope", ""),
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
    x_payload = _load_best_payload("x_latest.json")
    web_payload = _load_best_payload("web_latest.json")
    youtube_payload = _load_best_payload("youtube_latest.json")
    bilibili_payload = _load_best_payload("bilibili_latest.json")
    readiness_payload = _load_json(ROOT / "chapter2" / "output" / "filter_readiness.json")
    provider, provider_ready = _resolve_provider_state(
        readiness_payload, [x_payload, web_payload, youtube_payload, bilibili_payload]
    )

    items = []
    items.extend(_parse_x(x_payload))
    items.extend(_parse_generic(web_payload))
    items.extend(_parse_generic(youtube_payload, default_board="long_form"))
    items.extend(_parse_generic(bilibili_payload, default_board="long_form"))
    items.sort(key=lambda item: item.published_at or "", reverse=True)

    boards = {
        "direct_rss": [],
        "fast_news_and_leaks": [],
        "long_form": [],
    }
    for item in items:
        boards.setdefault(item.board, []).append(item)

    board_payload = {}
    for board, board_items in boards.items():
        published_items = [item.to_dict() for item in board_items if item.bucket == "published"]
        review_items = [item.to_dict() for item in board_items if item.bucket == "review"]
        board_payload[board] = {
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
        "boards": board_payload,
        "failures": _load_failures(),
    }
