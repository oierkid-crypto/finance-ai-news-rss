from __future__ import annotations

import os
import subprocess
import sys

from finance_ai_news.env import load_dotenv


COMMANDS = [
    ["python", "-m", "finance_ai_news.filter_readiness"],
    ["python", "-m", "finance_ai_news.fetch_x"],
    ["python", "-m", "finance_ai_news.fetch_web"],
    ["python", "-m", "finance_ai_news.fetch_youtube"],
    ["python", "-m", "finance_ai_news.fetch_bilibili"],
    ["python", "-m", "finance_ai_news.fetch_linkedin"],
    ["python", "-m", "finance_ai_news.reclassify_outputs"],
    ["python", "-m", "finance_ai_news.export_static_site", "--output", "docs"],
]


def run() -> int:
    load_dotenv()
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    for cmd in COMMANDS:
        print("running", " ".join(cmd))
        completed = subprocess.run(cmd, env=env)
        if completed.returncode != 0:
            print("command failed", " ".join(cmd), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
