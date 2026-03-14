from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from finance_ai_news.manifest import load_sources
from finance_ai_news.relevance.pipeline import apply_relevance_filter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-run semantic relevance filtering on existing Chapter 1 output files."
    )
    parser.add_argument(
        "--manifest",
        default="chapter1/day1_sources.json",
        help="Path to the source manifest JSON file.",
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Output JSON file to reclassify. May be repeated. Defaults to key Chapter 1 outputs.",
    )
    parser.add_argument(
        "--output-dir",
        default="chapter2/output/reclassified",
        help="Directory for reclassified output files.",
    )
    return parser.parse_args()


def default_inputs() -> List[str]:
    return [
        "chapter1/output/x_latest.json",
        "chapter1/output/web_latest.json",
        "chapter1/output/youtube_latest.json",
        "chapter1/output/bilibili_latest.json",
    ]


def collect_items(result: dict) -> List[dict]:
    return (
        result.get("accepted_items", [])
        + result.get("rejected_items", [])
        + result.get("review_items", [])
    )


def title_getter(item: dict) -> str:
    return item.get("title", "") or item.get("content", "")


def snippet_getter(item: dict) -> str:
    return item.get("content", "") or item.get("title", "")


def url_getter(item: dict) -> str:
    return item.get("url", "")


def run() -> int:
    args = parse_args()
    inputs = args.input or default_inputs()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_map = {source.id: source for source in load_sources(Path(args.manifest))}

    for input_file in inputs:
        input_path = Path(input_file)
        if not input_path.exists():
            continue

        payload = json.loads(input_path.read_text(encoding="utf-8"))
        reclassified_results = []
        for result in payload.get("results", []):
            source_id = result["source_id"]
            source = source_map.get(source_id)
            if not source:
                continue

            items = collect_items(result)
            filtered = apply_relevance_filter(
                source=source,
                raw_items=items,
                title_getter=title_getter,
                snippet_getter=snippet_getter,
                url_getter=url_getter,
            )
            reclassified_results.append(
                {
                    "source_id": source_id,
                    "source_name": result.get("source_name", source.name),
                    "reclassified_at": datetime.utcnow().isoformat() + "Z",
                    "filter_provider": filtered.provider,
                    "filter_provider_ready": filtered.provider_ready,
                    "raw_item_count": len(items),
                    "accepted_items": filtered.accepted_items,
                    "rejected_items": filtered.rejected_items,
                    "review_items": filtered.review_items,
                }
            )

        output_payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "input_file": str(input_path),
            "results": reclassified_results,
        }
        output_path = output_dir / input_path.name
        output_path.write_text(
            json.dumps(output_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"reclassified output written to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
