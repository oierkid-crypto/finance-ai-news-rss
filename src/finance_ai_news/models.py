from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Source:
    id: str
    name: str
    board: str
    region: str
    channel: str
    adapter: str
    importance: str
    notes: str = ""
    finance_scope: str = "finance_mixed"
    primary_url: Optional[str] = None
    fallback_url: Optional[str] = None
    handle: Optional[str] = None
    channel_handle: Optional[str] = None
    channel_id: Optional[str] = None
    uid: Optional[str] = None

    @classmethod
    def from_dict(cls, payload: dict) -> "Source":
        return cls(**payload)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


@dataclass
class SmokeTestResult:
    source_id: str
    source_name: str
    adapter: str
    board: str
    mode: str
    success: bool
    primary_path: str
    fallback_path: str
    checks: List[Check] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "adapter": self.adapter,
            "board": self.board,
            "mode": self.mode,
            "success": self.success,
            "primary_path": self.primary_path,
            "fallback_path": self.fallback_path,
            "checks": [
                {"name": check.name, "passed": check.passed, "detail": check.detail}
                for check in self.checks
            ],
            "notes": self.notes,
        }
