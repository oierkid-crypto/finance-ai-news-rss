from __future__ import annotations

from finance_ai_news.adapters.base import BaseAdapter
from finance_ai_news.models import Check, Source


class BilibiliAdapter(BaseAdapter):
    def smoke_test(self, source: Source):
        uid_present = bool(source.uid and source.uid != "0")
        uid_detail = source.uid or "missing"
        route = f"/bilibili/user/video/{source.uid}" if source.uid else "missing"

        checks = [
            Check("uid_present", uid_present, uid_detail),
            Check(
                "fallback_url_present",
                bool(source.fallback_url),
                source.fallback_url or "missing",
            ),
        ]
        success = all(check.passed for check in checks)
        notes = [
            "Bilibili is stable enough for Day 1, but each source needs a confirmed creator uid.",
            "A uid placeholder should fail smoke test so the source cannot silently slip into production.",
        ]

        return self.build_result(
            source=source,
            success=success,
            primary_path=f"RSSHub route {route}",
            fallback_path="creator page parser",
            checks=checks,
            notes=notes,
        )

