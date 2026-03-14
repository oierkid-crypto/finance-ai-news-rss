from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from finance_ai_news.env import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OLD_X_PROJECT_BACKEND = Path(
    "/Users/shaohua/Documents/AI/NewsFeed for Early Adopters/backend"
)


def resolve_x_python_bin() -> str:
    load_dotenv()
    env_value = os.environ.get("X_PYTHON_BIN")
    if env_value:
        return env_value

    old_venv_python = OLD_X_PROJECT_BACKEND / "venv" / "bin" / "python"
    if old_venv_python.exists():
        return str(old_venv_python)

    return sys.executable


def resolve_x_cookies_file() -> str:
    load_dotenv()
    env_value = os.environ.get("X_COOKIES_FILE")
    if env_value:
        return env_value

    local_cookies = PROJECT_ROOT / "data" / "cookies.json"
    if local_cookies.exists():
        return str(local_cookies)

    old_cookies = OLD_X_PROJECT_BACKEND / "data" / "cookies.json"
    if old_cookies.exists():
        return str(old_cookies)

    return str(local_cookies)


def check_twikit_available(python_bin: str) -> tuple[bool, str]:
    result = subprocess.run(
        [python_bin, "-c", "import importlib.util;print(bool(importlib.util.find_spec('twikit')))"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    output = (result.stdout or "").strip()
    return output == "True", f"{python_bin} -> twikit={output or 'unknown'}"
