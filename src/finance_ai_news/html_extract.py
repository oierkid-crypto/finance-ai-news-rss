from __future__ import annotations

import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from html import unescape


NAV_TITLE_PATTERNS = [
    "jump to content",
    "contact sales",
    "contact us",
    "get started",
    "sign in",
    "create account",
    "privacy",
    "terms",
    "cookie",
    "cookies",
    "language",
    "help",
    "marketplace",
]

NAV_URL_PATTERNS = [
    "/contact",
    "/privacy",
    "/terms",
    "/cookies",
    "/signup",
    "/signin",
    "/login",
    "/freetrial",
    "/account",
    "console.",
    "myaccount.",
]


def strip_tags(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return unescape(text).strip()


def extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.S | re.I)
    if not match:
        return ""
    return strip_tags(match.group(1))


def normalize_url(base_url: str, href: str) -> str:
    if not href:
        return ""
    href = unescape(href).strip()
    return urllib.parse.urljoin(base_url, href)


def _shared_path_score(base_url: str, url: str) -> int:
    base = urllib.parse.urlparse(base_url)
    candidate = urllib.parse.urlparse(url)
    base_parts = [part for part in base.path.split("/") if part]
    candidate_parts = [part for part in candidate.path.split("/") if part]
    overlap = len(set(base_parts) & set(candidate_parts))
    return min(overlap, 3)


def _link_score(base_url: str, title: str, url: str) -> int:
    lowered_title = title.lower()
    lowered_url = url.lower()
    parsed_base = urllib.parse.urlparse(base_url)
    parsed_url = urllib.parse.urlparse(url)

    score = 0
    if not title or len(title) < 12:
        score -= 4
    if 18 <= len(title) <= 160:
        score += 3
    elif len(title) <= 220:
        score += 1

    if parsed_base.netloc and parsed_url.netloc == parsed_base.netloc:
        score += 3

    depth = len([part for part in parsed_url.path.split("/") if part])
    score += min(depth, 4)
    score += _shared_path_score(base_url, url)

    if re.search(r"/20\d{2}/\d{2}/", parsed_url.path):
        score += 4
    if parsed_url.path.endswith(".html"):
        score += 4
    if re.search(r"/(article|articles|podcasts|post|posts|news|blog)/", parsed_url.path):
        score += 3
    if re.search(r"/p/[^/]+", parsed_url.path):
        score += 4
    if re.search(r"/watch\?v=", url):
        score += 4

    if parsed_url.fragment:
        score -= 4
    if parsed_url.path in {"", "/"}:
        score -= 4

    if any(pattern in lowered_title for pattern in NAV_TITLE_PATTERNS):
        score -= 6
    if any(pattern in lowered_url for pattern in NAV_URL_PATTERNS):
        score -= 6

    return score


def extract_structured_items(html: str, base_url: str, limit: int = 8) -> list[dict]:
    scripts = re.findall(
        r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        html,
        flags=re.S | re.I,
    )
    candidates: list[dict] = []

    def visit(node: object) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return

        node_type = node.get("@type")
        if isinstance(node_type, list):
            node_type = " ".join(str(item) for item in node_type)
        node_type = str(node_type or "")
        title = str(node.get("headline") or node.get("name") or "").strip()
        url = str(node.get("url") or node.get("@id") or "").strip()
        if title and url and any(
            kind in node_type.lower()
            for kind in ["article", "newsarticle", "blogposting", "podcastepisode", "videoobject"]
        ):
            candidates.append({"title": strip_tags(title)[:240], "url": normalize_url(base_url, url)})

        for key in ["itemListElement", "mainEntity", "mainEntityOfPage", "hasPart", "@graph"]:
            value = node.get(key)
            if value is not None:
                visit(value)

    for script in scripts:
        try:
            visit(json.loads(strip_tags(script)))
        except json.JSONDecodeError:
            continue

    deduped: list[dict] = []
    seen = set()
    for item in candidates:
        key = (item["title"], item["url"])
        if key in seen or not item["url"]:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def extract_links(html: str, base_url: str, limit: int = 8) -> list[dict]:
    structured = extract_structured_items(html, base_url, limit=limit)
    if structured:
        return structured

    matches = re.findall(
        r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        html,
        flags=re.S | re.I,
    )
    scored = []
    seen = set()
    for href, label in matches:
        text = strip_tags(label)
        if len(text) < 12:
            continue
        if href.startswith("#") or href.startswith("javascript:"):
            continue
        url = normalize_url(base_url, href)
        key = (text, url)
        if key in seen:
            continue
        seen.add(key)
        score = _link_score(base_url, text, url)
        if score <= 0:
            continue
        scored.append((score, {"title": text[:240], "url": url}))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item for _, item in scored[:limit]]


def normalize_feed_items(xml_text: str, limit: int = 8) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = []

    channel = root.find("./channel")
    if channel is not None:
        for item in channel.findall("./item")[:limit]:
            link = (item.findtext("link") or "").strip()
            guid = (item.findtext("guid") or "").strip()
            description = (
                item.findtext("description")
                or item.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}summary")
                or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded")
                or ""
            )
            enclosure = item.find("enclosure")
            enclosure_url = enclosure.attrib.get("url", "").strip() if enclosure is not None else ""
            items.append(
                {
                    "title": (item.findtext("title") or "").strip(),
                    "url": link or guid or enclosure_url,
                    "published": (item.findtext("pubDate") or "").strip(),
                    "description": strip_tags(description)[:400],
                }
            )
        return items

    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("./atom:entry", namespace)[:limit]:
        link = ""
        for link_node in entry.findall("./atom:link", namespace):
            href = link_node.attrib.get("href", "")
            rel = link_node.attrib.get("rel", "alternate")
            if href and rel == "alternate":
                link = href
                break
            if href and not link:
                link = href
        items.append(
            {
                "title": (entry.findtext("./atom:title", "", namespace) or "").strip(),
                "url": link.strip(),
                "published": (
                    entry.findtext("./atom:published", "", namespace)
                    or entry.findtext("./atom:updated", "", namespace)
                    or ""
                ).strip(),
                "description": strip_tags(
                    entry.findtext("./atom:summary", "", namespace)
                    or entry.findtext("./atom:content", "", namespace)
                    or ""
                )[:400],
            }
        )
    return items
