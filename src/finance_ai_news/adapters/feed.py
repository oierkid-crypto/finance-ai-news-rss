from __future__ import annotations

from finance_ai_news.adapters.base import BaseAdapter
from finance_ai_news.adapters.http_utils import fetch_url
from finance_ai_news.models import Check, Source


class FeedAdapter(BaseAdapter):
    def smoke_test(self, source: Source):
        checks = [
            Check("feed_url_present", bool(source.primary_url), source.primary_url or "missing"),
            Check("fallback_url_present", bool(source.fallback_url), source.fallback_url or "missing"),
        ]
        success = all(check.passed for check in checks)
        notes = ["Feeds are ideal for long-form and podcast adapters because parsing cost is low."]

        if self.mode == "live" and source.primary_url:
            ok, detail = fetch_url(source.primary_url)
            checks.append(Check("feed_url_reachable", ok, detail))
            success = success and ok

        return self.build_result(
            source=source,
            success=success,
            primary_path="native feed reader",
            fallback_path="HTML page parser",
            checks=checks,
            notes=notes,
        )

