from __future__ import annotations

from finance_ai_news.adapters.base import BaseAdapter
from finance_ai_news.adapters.http_utils import fetch_url
from finance_ai_news.models import Check, Source


class HtmlAdapter(BaseAdapter):
    def smoke_test(self, source: Source):
        checks = [
            Check("primary_url_present", bool(source.primary_url), source.primary_url or "missing"),
            Check("fallback_url_present", bool(source.fallback_url), source.fallback_url or "missing"),
        ]

        success = all(check.passed for check in checks)
        notes = ["HTML sources are the lowest-risk Day 1 ingestion family."]

        if self.mode == "live" and source.primary_url:
            ok, detail = fetch_url(source.primary_url)
            checks.append(Check("primary_url_reachable", ok, detail))
            success = success and ok

        return self.build_result(
            source=source,
            success=success,
            primary_path="custom HTML parser or custom RSSHub route",
            fallback_path="manual editor pick or generic page parser",
            checks=checks,
            notes=notes,
        )

