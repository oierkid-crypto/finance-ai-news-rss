from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime
from pathlib import Path

from finance_ai_news.html_extract import extract_links, extract_title, normalize_feed_items
from finance_ai_news.manifest import load_sources
from finance_ai_news.relevance.pipeline import apply_relevance_filter


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)


def fetch_text(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch HTML and feed based sources from the Day 1 source manifest."
    )
    parser.add_argument(
        "--manifest",
        default="chapter1/day1_sources.json",
        help="Path to the source manifest JSON file.",
    )
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Specific source id to fetch. May be repeated.",
    )
    parser.add_argument(
        "--output",
        default="chapter1/output/web_latest.json",
        help="Path to the output JSON file.",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sources = [
        source
        for source in load_sources(manifest_path)
        if source.adapter in {"html", "feed"}
    ]
    if args.source_id:
        wanted = set(args.source_id)
        sources = [source for source in sources if source.id in wanted]

    results = []
    failures = []
    for source in sources:
        try:
            used_url = source.primary_url
            used_path = "primary"
            try:
                body = fetch_text(source.primary_url)
            except Exception:
                if not source.fallback_url:
                    raise
                body = fetch_text(source.fallback_url)
                used_url = source.fallback_url
                used_path = "fallback"

            if source.adapter == "feed":
                try:
                    items = normalize_feed_items(body)
                    title = items[0]["title"] if items else source.name
                except Exception:
                    if not source.fallback_url or used_path == "fallback":
                        raise
                    body = fetch_text(source.fallback_url)
                    used_url = source.fallback_url
                    used_path = "fallback"
                    title = extract_title(body) or source.name
                    items = extract_links(body, base_url=used_url)
            else:
                title = extract_title(body) or source.name
                items = extract_links(body, base_url=used_url)

            filtered = apply_relevance_filter(
                source=source,
                raw_items=items,
                title_getter=lambda item: item.get("title", ""),
                snippet_getter=lambda item: " ".join(
                    part.strip()
                    for part in [
                        item.get("description", ""),
                        f"Source context: {source.name}.",
                        source.notes,
                        f"Listing page: {title}.",
                    ]
                    if part and part.strip()
                ),
                url_getter=lambda item: item.get("url", ""),
            )

            results.append(
                {
                    "source_id": source.id,
                    "source_name": source.name,
                    "board": source.board,
                    "adapter": source.adapter,
                    "fetched_at": datetime.utcnow().isoformat() + "Z",
                    "used_path": used_path,
                    "used_url": used_url,
                    "page_title": title,
                    "filter_provider": filtered.provider,
                    "filter_provider_ready": filtered.provider_ready,
                    "raw_item_count": len(items),
                    "accepted_items": filtered.accepted_items,
                    "rejected_items": filtered.rejected_items,
                    "review_items": filtered.review_items,
                }
            )
        except Exception as exc:
            failures.append(
                {
                    "source_id": source.id,
                    "source_name": source.name,
                    "error": str(exc),
                }
            )

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "results": results,
        "failures": failures,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"output written to {output_path}")
    print(f"sources={len(sources)} successes={len(results)} failures={len(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(run())
