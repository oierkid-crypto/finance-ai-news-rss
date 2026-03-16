from __future__ import annotations

from xml.sax.saxutils import escape

from finance_ai_news.taxonomy import get_board_definition


def _escape_html(text: str) -> str:
    return escape((text or "").replace("\r\n", "\n").replace("\r", "\n"))


def _render_tag_line(item: dict) -> str:
    tags = item.get("tags", {})
    blocks = []
    region = tags.get("region", [])
    industry = tags.get("industry", [])
    institution = tags.get("institution", [])
    if region:
        blocks.append(f"地域：{' / '.join(_escape_html(tag) for tag in region)}")
    if industry:
        blocks.append(f"行业：{' / '.join(_escape_html(tag) for tag in industry)}")
    if institution:
        blocks.append(f"机构：{' / '.join(_escape_html(tag) for tag in institution)}")
    if not blocks:
        return ""
    return "<p><strong>标签</strong> " + " | ".join(blocks) + "</p>"


def _build_item_html(item: dict) -> str:
    snippet = _escape_html(item.get("snippet", "")).replace("\n", "<br />")
    url = escape(item.get("url", ""))
    section = _escape_html(item.get("section_title", ""))
    subtitle = _escape_html(item.get("section_subtitle", ""))
    section_html = ""
    if section:
        section_html = f"<p><strong>栏目</strong> {section}"
        if subtitle:
            section_html += f" <em>({subtitle})</em>"
        section_html += "</p>"
    link_html = ""
    if url:
        link_html = (
            '<br /><br />'
            "原文链接："
            f'<a href="{url}" style="color:#1f5eff;font-style:italic;text-decoration:underline;">'
            f"{url}"
            "</a>"
        )
    return f"<div>{section_html}{_render_tag_line(item)}<p>{snippet}{link_html}</p></div>"


def build_combined_items(state: dict) -> list[dict]:
    items = []
    for board in state.get("boards", {}).values():
        items.extend(board.get("delivery", []))
    items.sort(key=lambda item: item.get("published_at", ""), reverse=True)
    return items


def build_feed_xml(base_url: str, board_name: str, items: list[dict], preview: bool) -> str:
    definition = get_board_definition(board_name)
    title_suffix = "Preview" if preview else "Published"
    if board_name == "all":
        feed_title = f"FinAI 全部栏目 Feed ({title_suffix})"
        feed_description = "Combined feed for all FinAI sections"
    else:
        feed_title = f"{definition.title} | {definition.subtitle} ({title_suffix})"
        feed_description = definition.description
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">',
        "<channel>",
        f"<title>{escape(feed_title)}</title>",
        f"<link>{escape(base_url)}</link>",
        f"<description>{escape(feed_description)}</description>",
    ]
    for item in items:
        html_description = _build_item_html(item)
        categories = [item.get("section_title", ""), item.get("bucket", "review")]
        categories.extend(item.get("tags", {}).get("all", []))
        category_xml = "\n".join(
            f"<category>{escape(category)}</category>" for category in categories if category
        )
        lines.extend(
            [
                "<item>",
                f"<title>{escape(item.get('title', 'Untitled'))}</title>",
                f"<link>{escape(item.get('url', ''))}</link>",
                f"<guid>{escape(item.get('id', item.get('url', '')))}</guid>",
                f"<description><![CDATA[{html_description}]]></description>",
                f"<content:encoded><![CDATA[{html_description}]]></content:encoded>",
                category_xml,
                f"<pubDate>{escape(item.get('published_at', ''))}</pubDate>",
                "</item>",
            ]
        )
    lines.extend(["</channel>", "</rss>"])
    return "\n".join(lines)
