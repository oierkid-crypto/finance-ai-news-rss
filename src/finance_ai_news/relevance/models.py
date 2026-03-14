from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Candidate:
    candidate_id: str
    source_id: str
    source_name: str
    board: str
    channel: str
    title: str
    snippet: str
    url: str
    metadata: Dict[str, str]


@dataclass
class Decision:
    candidate_id: str
    verdict: str
    provider: str
    reason: str
    confidence: str = "unknown"

    def to_dict(self) -> Dict[str, str]:
        return {
            "candidate_id": self.candidate_id,
            "verdict": self.verdict,
            "provider": self.provider,
            "reason": self.reason,
            "confidence": self.confidence,
        }


@dataclass
class FilteredBatch:
    provider: str
    provider_ready: bool
    accepted_items: List[dict]
    rejected_items: List[dict]
    review_items: List[dict]
    decisions: List[Decision]

