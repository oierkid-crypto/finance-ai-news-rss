from __future__ import annotations

from pathlib import Path

from finance_ai_news.adapters.base import BaseAdapter
from finance_ai_news.models import Check, Source
from finance_ai_news.runtime import (
    check_twikit_available,
    resolve_x_cookies_file,
    resolve_x_python_bin,
)


class XAccountAdapter(BaseAdapter):
    def smoke_test(self, source: Source):
        python_bin = resolve_x_python_bin()
        cookie_path = resolve_x_cookies_file()
        cookie_exists = Path(cookie_path).exists()
        twikit_available, twikit_detail = check_twikit_available(python_bin)

        checks = [
            Check("handle_present", bool(source.handle), source.handle or "missing"),
            Check("python_bin_present", bool(python_bin), python_bin),
            Check("twikit_available", twikit_available, twikit_detail),
            Check(
                "cookie_path_configured",
                bool(cookie_path),
                f"X_COOKIES_FILE={cookie_path}",
            ),
            Check("cookie_file_exists", cookie_exists, cookie_path),
        ]
        success = checks[0].passed and checks[1].passed and checks[2].passed and checks[4].passed
        notes = [
            "Best for curated whitelists, not whole-platform crawling.",
            "The old project already validated the twikit plus cookies pattern.",
            "This adapter can reuse an external Python runtime if twikit is not installed in the current interpreter.",
        ]

        if self.mode == "live":
            notes.append(
                "Use python -m finance_ai_news.fetch_x for real account fetches after smoke test passes."
            )

        return self.build_result(
            source=source,
            success=success,
            primary_path="twikit + cookies + whitelist filters",
            fallback_path="RSSHub Twitter route or Playwright validation",
            checks=checks,
            notes=notes,
        )
