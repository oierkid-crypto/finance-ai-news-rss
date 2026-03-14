from __future__ import annotations

import json
from pathlib import Path

from finance_ai_news.env import load_dotenv
from finance_ai_news.relevance.models import Candidate
from finance_ai_news.relevance.provider import build_classifier


def run() -> int:
    load_dotenv()
    classifier = build_classifier()

    report = {
        "provider": classifier.provider_name,
        "is_ready": classifier.is_ready(),
        "ok": False,
        "error": "",
        "decision": None,
    }

    if classifier.is_ready():
        try:
            decisions = classifier.classify(
                [
                    Candidate(
                        candidate_id="probe-1",
                        source_id="probe",
                        source_name="Provider Probe",
                        board="system",
                        channel="probe",
                        title="BBVA expands AI banking collaboration",
                        snippet="A minimal AI x Finance probe request.",
                        url="https://example.com/probe",
                        metadata={},
                    )
                ]
            )
            report["ok"] = True
            if decisions:
                report["decision"] = decisions[0].to_dict()
        except Exception as exc:
            report["error"] = str(exc)

    output_path = Path("chapter2/output/provider_probe.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"output written to {output_path}")
    print(f"provider={report['provider']} ready={report['is_ready']} ok={report['ok']}")
    if report["error"]:
        print(report["error"])
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
