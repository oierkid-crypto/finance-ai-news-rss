from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from finance_ai_news.models import Check, SmokeTestResult, Source


class BaseAdapter(ABC):
    mode: str

    def __init__(self, mode: str = "dry-run") -> None:
        self.mode = mode

    @abstractmethod
    def smoke_test(self, source: Source) -> SmokeTestResult:
        raise NotImplementedError

    def build_result(
        self,
        source: Source,
        success: bool,
        primary_path: str,
        fallback_path: str,
        checks: List[Check],
        notes: Optional[List[str]] = None,
    ) -> SmokeTestResult:
        return SmokeTestResult(
            source_id=source.id,
            source_name=source.name,
            adapter=source.adapter,
            board=source.board,
            mode=self.mode,
            success=success,
            primary_path=primary_path,
            fallback_path=fallback_path,
            checks=checks,
            notes=notes or [],
        )
