from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

from twikit import Client


async def fetch_account(handle: str, cookies_file: str, count: int) -> dict:
    client = Client("en-US")
    client.load_cookies(cookies_file)

    user = await client.get_user_by_screen_name(handle)
    tweets = await user.get_tweets("Tweets", count=count)

    items = []
    for tweet in tweets or []:
        text = getattr(tweet, "text", "") or ""
        if text.startswith("RT @") or text.startswith("@"):
            continue
        items.append(
            {
                "id": str(tweet.id),
                "handle": handle,
                "name": user.name,
                "content": text,
                "created_at": tweet.created_at or datetime.utcnow().isoformat() + "Z",
                "url": f"https://x.com/{handle}/status/{tweet.id}",
            }
        )

    return {"handle": handle, "items": items}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch X timeline with twikit.")
    parser.add_argument("--handle", required=True)
    parser.add_argument("--cookies-file", required=True)
    parser.add_argument("--count", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = asyncio.run(fetch_account(args.handle, args.cookies_file, args.count))
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
