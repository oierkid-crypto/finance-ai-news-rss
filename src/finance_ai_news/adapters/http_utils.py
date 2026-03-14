from __future__ import annotations

import urllib.error
import urllib.request


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)


def fetch_url(url: str, timeout: int = 20):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            status = getattr(response, "status", 200)
            body = response.read(1024)
            return True, f"status={status}, content_type={content_type}, sample_bytes={len(body)}"
    except urllib.error.HTTPError as exc:
        return False, f"http_error={exc.code}"
    except urllib.error.URLError as exc:
        return False, f"url_error={exc.reason}"
