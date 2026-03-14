from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from finance_ai_news.env import load_dotenv
from finance_ai_news.product import load_dashboard_state
from finance_ai_news.rss import build_combined_items, build_feed_xml


ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "web"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the dashboard and feeds as a static site for GitHub Pages."
    )
    parser.add_argument(
        "--output",
        default="docs",
        help="Directory to write the static site into.",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Public site base URL. Defaults to PUBLIC_BASE_URL or a GitHub Pages URL derived from GITHUB_REPOSITORY.",
    )
    return parser.parse_args()


def derive_base_url(explicit: str) -> str:
    if explicit:
        return explicit.rstrip("/")

    env_url = os.environ.get("PUBLIC_BASE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")

    github_repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if github_repository and "/" in github_repository:
        owner, repo = github_repository.split("/", 1)
        return f"https://{owner}.github.io/{repo}"

    return "https://example.com/finance-ai-news-rss"


def render_static_index() -> str:
    html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    replacements = {
        'href="/assets/styles.css"': 'href="./assets/styles.css"',
        'href="/feeds/all.xml"': 'href="./feeds/all.xml"',
        'href="/feeds/direct_rss.xml"': 'href="./feeds/direct_rss.xml"',
        'href="/feeds/fast_news_and_leaks.xml"': 'href="./feeds/fast_news_and_leaks.xml"',
        'href="/feeds/long_form.xml"': 'href="./feeds/long_form.xml"',
        'src="/assets/app.js"': 'src="./assets/app.js"',
    }
    for before, after in replacements.items():
        html = html.replace(before, after)
    return html


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def export_site(output_dir: Path, base_url: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    data_dir = output_dir / "data"
    feeds_dir = output_dir / "feeds"
    boards_dir = data_dir / "boards"

    assets_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    feeds_dir.mkdir(parents=True, exist_ok=True)
    boards_dir.mkdir(parents=True, exist_ok=True)

    state = load_dashboard_state()

    (output_dir / "index.html").write_text(render_static_index(), encoding="utf-8")
    shutil.copy2(WEB_DIR / "app.js", assets_dir / "app.js")
    shutil.copy2(WEB_DIR / "styles.css", assets_dir / "styles.css")
    write_json(data_dir / "dashboard.json", state)
    write_json(data_dir / "failures.json", state.get("failures", []))

    for board_name, board_payload in state.get("boards", {}).items():
        write_json(boards_dir / f"{board_name}.json", board_payload)
        xml = build_feed_xml(
            base_url=f"{base_url}/feeds/{board_name}.xml",
            board_name=board_name,
            items=board_payload.get("delivery", []),
            preview=not state.get("provider_ready", False),
        )
        (feeds_dir / f"{board_name}.xml").write_text(xml, encoding="utf-8")

    combined_xml = build_feed_xml(
        base_url=f"{base_url}/feeds/all.xml",
        board_name="all",
        items=build_combined_items(state),
        preview=not state.get("provider_ready", False),
    )
    (feeds_dir / "all.xml").write_text(combined_xml, encoding="utf-8")

    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    (output_dir / "404.html").write_text(render_static_index(), encoding="utf-8")

    cname = os.environ.get("PAGES_CNAME", "").strip()
    if cname:
        (output_dir / "CNAME").write_text(cname + "\n", encoding="utf-8")


def run() -> int:
    load_dotenv()
    args = parse_args()
    output_dir = ROOT / args.output
    base_url = derive_base_url(args.base_url)
    export_site(output_dir, base_url)
    print(f"static site written to {output_dir}")
    print(f"base_url={base_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
