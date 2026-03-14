from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
import urllib.request

from finance_ai_news.html_extract import extract_links
from finance_ai_news.manifest import load_sources
from finance_ai_news.relevance.pipeline import apply_relevance_filter


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)


def _run_ytdlp(cmd: list[str]):
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip())
    return completed.stdout


def fetch_channel(channel_target: str, limit: int, browser: str):
    if channel_target.startswith("@"):
        channel_url = f"https://www.youtube.com/{channel_target}/videos"
    elif channel_target.startswith("UC"):
        channel_url = f"https://www.youtube.com/channel/{channel_target}/videos"
    else:
        channel_url = channel_target

    base_cmd = [
        "yt-dlp",
        "--no-update",
        "--dump-json",
        "--flat-playlist",
        "--playlist-end",
        str(limit),
        "--extractor-args",
        "youtubetab:skip=authcheck",
        channel_url,
    ]
    try:
        stdout = _run_ytdlp(
            [
                *base_cmd[:-1],
                "--cookies-from-browser",
                browser,
                base_cmd[-1],
            ]
        )
    except Exception:
        stdout = _run_ytdlp(base_cmd)

    items = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        video_id = payload.get("id", "")
        items.append(
            {
                "video_id": video_id,
                "title": payload.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "upload_date": payload.get("upload_date", ""),
                "description": payload.get("description", ""),
            }
        )
    return items


def fetch_text(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube sources from the Day 1 source manifest."
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
        "--limit",
        type=int,
        default=3,
        help="Maximum number of latest videos to fetch per source.",
    )
    parser.add_argument(
        "--output",
        default="chapter1/output/youtube_latest.json",
        help="Path to the output JSON file.",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    browser = os.environ.get("YTDLP_BROWSER", "chrome")

    sources = [
        source
        for source in load_sources(manifest_path)
        if source.adapter == "youtube"
    ]
    if args.source_id:
        wanted = set(args.source_id)
        sources = [source for source in sources if source.id in wanted]

    results = []
    failures = []
    for source in sources:
        try:
            channel_target = source.channel_id or source.channel_handle
            used_path = "primary"
            try:
                items = fetch_channel(channel_target, args.limit, browser)
            except Exception:
                if not source.fallback_url:
                    raise
                html = fetch_text(source.fallback_url)
                items = extract_links(html, base_url=source.fallback_url, limit=args.limit)
                used_path = "fallback"
            filtered = apply_relevance_filter(
                source=source,
                raw_items=items,
                title_getter=lambda item: item.get("title", ""),
                snippet_getter=lambda item: item.get("description", "") or source.name,
                url_getter=lambda item: item.get("url", ""),
            )
            results.append(
                {
                    "source_id": source.id,
                    "source_name": source.name,
                    "channel_target": channel_target,
                    "fetched_at": datetime.utcnow().isoformat() + "Z",
                    "used_path": used_path,
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
        "browser": browser,
        "results": results,
        "failures": failures,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"output written to {output_path}")
    print(f"sources={len(sources)} successes={len(results)} failures={len(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(run())
