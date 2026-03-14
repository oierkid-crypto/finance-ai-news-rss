from __future__ import annotations

from xml.sax.saxutils import escape


def build_feed_xml(base_url: str, board_name: str, items: list[dict], preview: bool) -> str:
    title_suffix = "Preview" if preview else "Published"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        "<channel>",
        f"<title>{escape(board_name)} Feed ({title_suffix})</title>",
        f"<link>{escape(base_url)}</link>",
        f"<description>{escape(board_name)} feed for the AI x Finance product</description>",
    ]
    for item in items:
        description = item.get("snippet", "")
        lines.extend(
            [
                "<item>",
                f"<title>{escape(item.get('title', 'Untitled'))}</title>",
                f"<link>{escape(item.get('url', ''))}</link>",
                f"<guid>{escape(item.get('id', item.get('url', '')))}</guid>",
                f"<description>{escape(description)}</description>",
                f"<category>{escape(item.get('bucket', 'review'))}</category>",
                f"<pubDate>{escape(item.get('published_at', ''))}</pubDate>",
                "</item>",
            ]
        )
    lines.extend(["</channel>", "</rss>"])
    return "\n".join(lines)
