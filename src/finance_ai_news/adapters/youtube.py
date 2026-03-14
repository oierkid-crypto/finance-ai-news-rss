from __future__ import annotations

import os
import shutil

from finance_ai_news.adapters.base import BaseAdapter
from finance_ai_news.models import Check, Source


class YouTubeAdapter(BaseAdapter):
    def smoke_test(self, source: Source):
        yt_dlp_present = shutil.which("yt-dlp") is not None
        channel_target = source.channel_handle or source.channel_id or ""
        cookies_browser = os.environ.get("YTDLP_BROWSER", "chrome")

        checks = [
            Check("channel_target_present", bool(channel_target), channel_target or "missing"),
            Check("yt_dlp_available", yt_dlp_present, "yt-dlp in PATH"),
            Check(
                "cookies_browser_configured",
                bool(cookies_browser),
                f"YTDLP_BROWSER={cookies_browser}",
            ),
            Check(
                "fallback_url_present",
                bool(source.fallback_url),
                source.fallback_url or "missing",
            ),
        ]
        success = all(check.passed for check in checks[:2])
        notes = [
            "Primary path should reuse the old project pattern: yt-dlp for list fetch and transcript fetch.",
            "Fallback path is native YouTube feed once channel_id is known.",
        ]

        if source.channel_id:
            notes.append(
                f"Native feed candidate: https://www.youtube.com/feeds/videos.xml?channel_id={source.channel_id}"
            )

        return self.build_result(
            source=source,
            success=success,
            primary_path="yt-dlp channel fetcher + transcript extraction",
            fallback_path="native YouTube channel feed",
            checks=checks,
            notes=notes,
        )

