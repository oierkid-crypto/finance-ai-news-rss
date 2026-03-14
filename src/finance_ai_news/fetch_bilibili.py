from __future__ import annotations

import argparse
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from pathlib import Path

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


def strip_tags(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return unescape(text).strip()


def extract_video_links(html: str, limit: int = 8):
    matches = re.findall(
        r"<a[^>]+href=[\"']([^\"']*?/video/[^\"']+)[\"'][^>]*>(.*?)</a>",
        html,
        flags=re.S | re.I,
    )
    items = []
    seen = set()
    for href, label in matches:
        url = href if href.startswith("http") else "https:" + href if href.startswith("//") else "https://www.bilibili.com" + href
        if url in seen:
            continue
        seen.add(url)
        text = strip_tags(label)
        if len(text) < 4:
            continue
        items.append({"title": text[:200], "url": url})
        if len(items) >= limit:
            break
    return items


def parse_feed_items(xml_text: str, limit: int = 8):
    root = ET.fromstring(xml_text)
    items = []
    channel = root.find("./channel")
    if channel is None:
        return items
    for item in channel.findall("./item")[:limit]:
        items.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "url": (item.findtext("link") or "").strip(),
                "published": (item.findtext("pubDate") or "").strip(),
            }
        )
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Bilibili sources from the Day 1 source manifest.")
    parser.add_argument(
        "--manifest",
        default="chapter1/day1_sources.json",
        help="Path to the source manifest JSON file.",
    )
    parser.add_argument(
        "--output",
        default="chapter1/output/bilibili_latest.json",
        help="Path to the output JSON file.",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sources = [source for source in load_sources(manifest_path) if source.adapter == "bilibili"]

    results = []
    failures = []
    for source in sources:
        url = source.fallback_url or f"https://space.bilibili.com/{source.uid}/video"
        rsshub_url = f"https://rsshub.app/bilibili/user/video/{source.uid}"
        try:
            html = fetch_text(url)
            items = extract_video_links(html)
            used_path = "page"
            used_url = url
            if not items:
                feed = fetch_text(rsshub_url)
                items = parse_feed_items(feed)
                used_path = "rsshub"
                used_url = rsshub_url
            filtered = apply_relevance_filter(
                source=source,
                raw_items=items,
                title_getter=lambda item: item.get("title", ""),
                snippet_getter=lambda item: source.name,
                url_getter=lambda item: item.get("url", ""),
            )
            results.append(
                {
                    "source_id": source.id,
                    "source_name": source.name,
                    "uid": source.uid,
                    "fetched_at": datetime.utcnow().isoformat() + "Z",
                    "used_path": used_path,
                    "used_url": used_url,
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
                    "uid": source.uid,
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
