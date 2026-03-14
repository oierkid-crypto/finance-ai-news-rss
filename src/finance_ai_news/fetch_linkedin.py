from __future__ import annotations

import argparse
import importlib.util
import json
import os
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LinkedIn pilot-source readiness for browser-based fetching."
    )
    parser.add_argument(
        "--manifest",
        default="chapter1/linkedin_sources.json",
        help="Path to the LinkedIn source manifest JSON file.",
    )
    parser.add_argument(
        "--output",
        default="chapter1/output/linkedin_readiness.json",
        help="Path to the output JSON file.",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = payload["sources"]
    playwright_installed = importlib.util.find_spec("playwright") is not None
    storage_state = os.environ.get("LINKEDIN_STORAGE_STATE", "")

    results = []
    for source in sources:
        results.append(
            {
                "source_id": source["id"],
                "name": source["name"],
                "type": source["type"],
                "url": source["url"],
                "priority": source["priority"],
                "ready_for_live_fetch": bool(playwright_installed and storage_state),
                "needs_login_state": True,
                "playwright_installed": playwright_installed,
                "storage_state_configured": bool(storage_state),
                "recommended_path": "Playwright logged-in session for pilot-only fetching",
            }
        )

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "playwright_installed": playwright_installed,
        "linkedin_storage_state": storage_state,
        "results": results,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"output written to {output_path}")
    print(f"sources={len(results)} ready={sum(1 for item in results if item['ready_for_live_fetch'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
