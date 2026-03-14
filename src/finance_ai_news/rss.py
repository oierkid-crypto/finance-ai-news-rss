from __future__ import annotations

from xml.sax.saxutils import escape


def _escape_html(text: str) -> str:
    return escape((text or "").replace("\r\n", "\n").replace("\r", "\n"))


def _build_item_html(item: dict) -> str:
    snippet = _escape_html(item.get("snippet", "")).replace("\n", "<br />")
    url = escape(item.get("url", ""))
    link_html = ""
    if url:
        link_html = (
            f'<p style="margin:14px 0 0;">'
            f'<a href="{url}" style="color:#1f5eff;font-style:italic;text-decoration:underline;">'
            "原文链接"
            "</a></p>"
        )
    return f"<div><p>{snippet}</p>{link_html}</div>"


def build_combined_items(state: dict) -> list[dict]:
    items = []
    for board in state.get("boards", {}).values():
        items.extend(board.get("delivery", []))
    items.sort(key=lambda item: item.get("published_at", ""), reverse=True)
    return items


def build_feed_xml(base_url: str, board_name: str, items: list[dict], preview: bool) -> str:
    title_suffix = "Preview" if preview else "Published"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">',
        "<channel>",
        f"<title>{escape(board_name)} Feed ({title_suffix})</title>",
        f"<link>{escape(base_url)}</link>",
        f"<description>{escape(board_name)} feed for the AI x Finance product</description>",
    ]
    for item in items:
        html_description = _build_item_html(item)
        lines.extend(
            [
                "<item>",
                f"<title>{escape(item.get('title', 'Untitled'))}</title>",
                f"<link>{escape(item.get('url', ''))}</link>",
                f"<guid>{escape(item.get('id', item.get('url', '')))}</guid>",
                f"<description><![CDATA[{html_description}]]></description>",
                f"<content:encoded><![CDATA[{html_description}]]></content:encoded>",
                f"<category>{escape(item.get('bucket', 'review'))}</category>",
                f"<pubDate>{escape(item.get('published_at', ''))}</pubDate>",
                "</item>",
            ]
        )
    lines.extend(["</channel>", "</rss>"])
    return "\n".join(lines)
