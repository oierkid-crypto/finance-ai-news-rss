from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from finance_ai_news.adapters import ADAPTERS
from finance_ai_news.manifest import filter_day1_core, load_sources


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test Chapter 1 source adapters for the AI x Finance RSS project."
    )
    parser.add_argument(
        "--manifest",
        default="chapter1/day1_sources.json",
        help="Path to the source manifest JSON file.",
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "live"],
        default="dry-run",
        help="Dry-run only checks adapter prerequisites. Live also performs safe network reachability checks where supported.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test every source in the manifest. Default behavior only tests P0 sources.",
    )
    parser.add_argument(
        "--output",
        default="chapter1/output/smoke_test_report.json",
        help="Path to the JSON report file.",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sources = load_sources(manifest_path)
    if not args.all:
        sources = filter_day1_core(sources)

    results = []
    passed = 0

    for source in sources:
        adapter_cls = ADAPTERS[source.adapter]
        adapter = adapter_cls(mode=args.mode)
        result = adapter.smoke_test(source)
        results.append(result.to_dict())
        if result.success:
            passed += 1

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "manifest": str(manifest_path),
        "mode": args.mode,
        "tested_sources": len(results),
        "passed_sources": passed,
        "failed_sources": len(results) - passed,
        "results": results,
    }
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"report written to {output_path}")
    print(f"tested={report['tested_sources']} passed={report['passed_sources']} failed={report['failed_sources']}")
    return 0 if report["failed_sources"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run())
