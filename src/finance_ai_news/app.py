from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from finance_ai_news.product import load_dashboard_state
from finance_ai_news.rss import build_feed_xml


ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "web"

app = FastAPI(title="AI x Finance RSS")
app.mount("/assets", StaticFiles(directory=str(WEB_DIR)), name="assets")


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/dashboard")
def dashboard() -> JSONResponse:
    return JSONResponse(load_dashboard_state())


@app.get("/api/boards/{board}")
def board(board: str) -> JSONResponse:
    state = load_dashboard_state()
    board_data = state["boards"].get(board)
    if board_data is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return JSONResponse(board_data)


@app.get("/api/failures")
def failures() -> JSONResponse:
    return JSONResponse(load_dashboard_state()["failures"])


@app.post("/api/refresh")
def refresh() -> JSONResponse:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    subprocess.Popen(
        [sys.executable, "-m", "finance_ai_news.refresh_all"],
        cwd=str(ROOT),
        env=env,
    )
    return JSONResponse({"status": "started"})


@app.get("/feeds/{board}.xml")
def feed(board: str, request: Request) -> PlainTextResponse:
    state = load_dashboard_state()
    board_data = state["boards"].get(board)
    if board_data is None:
        raise HTTPException(status_code=404, detail="Board not found")
    items = board_data["delivery"]
    xml = build_feed_xml(
        base_url=str(request.url),
        board_name=board,
        items=items,
        preview=not state["provider_ready"],
    )
    return PlainTextResponse(content=xml, media_type="application/rss+xml")
