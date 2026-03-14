from __future__ import annotations

import json
import os
from pathlib import Path

from finance_ai_news.env import load_dotenv
from finance_ai_news.relevance.models import Candidate
from finance_ai_news.relevance.provider import build_classifier


def run() -> int:
    load_dotenv()
    classifier = build_classifier()
    provider_ready = classifier.is_ready()
    provider_error = ""

    if provider_ready:
        try:
            classifier.classify(
                [
                    Candidate(
                        candidate_id="readiness-check",
                        source_id="system",
                        source_name="System Readiness Check",
                        board="system",
                        channel="healthcheck",
                        title="OpenAI expands BBVA collaboration for banking agents",
                        snippet="A short healthcheck classification request for the AI x Finance pipeline.",
                        url="https://example.com/readiness",
                        metadata={},
                    )
                ]
            )
        except Exception as exc:
            provider_ready = False
            provider_error = str(exc)

    report = {
        "provider": classifier.provider_name,
        "provider_ready": provider_ready,
        "provider_error": provider_error,
        "env": {
            "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
            "OPENAI_BASE_URL": os.environ.get("OPENAI_BASE_URL", ""),
            "OPENAI_MODEL": os.environ.get("OPENAI_MODEL", ""),
        },
    }

    output_path = Path("chapter2/output/filter_readiness.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"output written to {output_path}")
    print(
        "provider={} ready={}".format(
            report["provider"], report["provider_ready"]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
