from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from finance_ai_news.manifest import load_sources
from finance_ai_news.relevance.pipeline import apply_relevance_filter
from finance_ai_news.runtime import (
    PROJECT_ROOT,
    resolve_x_cookies_file,
    resolve_x_python_bin,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch selected X accounts from the Day 1 source manifest."
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
        "--count",
        type=int,
        default=8,
        help="Maximum tweets to request per account before filtering.",
    )
    parser.add_argument(
        "--output",
        default="chapter1/output/x_latest.json",
        help="Path to the output JSON file.",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sources = [source for source in load_sources(manifest_path) if source.adapter == "x_account"]
    if args.source_id:
        wanted = set(args.source_id)
        sources = [source for source in sources if source.id in wanted]

    python_bin = resolve_x_python_bin()
    cookies_file = resolve_x_cookies_file()

    results = []
    failures = []
    for source in sources:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        cmd = [
            python_bin,
            "-m",
            "finance_ai_news.x_runtime_fetch",
            "--handle",
            source.handle,
            "--cookies-file",
            cookies_file,
            "--count",
            str(args.count),
        ]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )
            if completed.returncode != 0:
                failures.append(
                    {
                        "source_id": source.id,
                        "handle": source.handle,
                        "error": (completed.stderr or completed.stdout).strip(),
                    }
                )
                continue

            payload = json.loads(completed.stdout)
            filtered = apply_relevance_filter(
                source=source,
                raw_items=payload.get("items", []),
                title_getter=lambda item: item.get("content", ""),
                snippet_getter=lambda item: item.get("content", ""),
                url_getter=lambda item: item.get("url", ""),
            )
            results.append(
                {
                    "source_id": source.id,
                    "source_name": source.name,
                    "handle": source.handle,
                    "fetched_at": datetime.utcnow().isoformat() + "Z",
                    "filter_provider": filtered.provider,
                    "filter_provider_ready": filtered.provider_ready,
                    "raw_item_count": len(payload.get("items", [])),
                    "accepted_items": filtered.accepted_items,
                    "rejected_items": filtered.rejected_items,
                    "review_items": filtered.review_items,
                }
            )
        except Exception as exc:
            failures.append(
                {
                    "source_id": source.id,
                    "handle": source.handle,
                    "error": str(exc),
                }
            )

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "python_bin": python_bin,
        "cookies_file": cookies_file,
        "results": results,
        "failures": failures,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"output written to {output_path}")
    print(f"accounts={len(sources)} successes={len(results)} failures={len(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(run())
