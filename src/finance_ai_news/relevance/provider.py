from __future__ import annotations

import json
import os
import re
import time
import urllib.request
import urllib.error
from typing import List

from finance_ai_news.env import load_dotenv
from finance_ai_news.relevance.models import Candidate, Decision


SYSTEM_PROMPT = """You are the editorial gate for an AI x Finance news product.

Decide whether each candidate is publishable for readers who only care about the intersection of:
1. AI: machine learning, LLMs, agents, model deployment, AI infrastructure, AI operations, or AI-enabled workflows
2. Finance: banks, payments, insurance, lending, wealth, asset management, capital markets, regulatory technology, or named financial institutions / fintechs

Use the candidate's source context. Every item includes a finance_scope:
- finance_dedicated: the source itself is dedicated to finance or fintech. You may treat finance context as satisfied by the source, but only if the item itself is materially about AI or AI-enabled operational change.
- finance_mixed: the source often covers finance, but not always. Accept only if the item is materially about AI and plausibly impacts finance workflows.
- require_explicit_finance: the source is general AI or general tech. Accept only if the item itself clearly points to a financial institution, fintech, payments, insurance, markets, lending, compliance, or regulation.

Editorial rules:
- Reject generic AI product launches, model evaluations, hiring posts, security tooling, or research updates when the finance link is missing.
- Reject items that are mostly about general cloud modernization, databases, or infrastructure unless AI is central to the story.
- If the title/snippet is too thin to know, return review.
- Do not rely on literal keyword matching only. Use semantic meaning and source context together.

Return JSON only in this shape:
{"results":[{"candidate_id":"...","verdict":"accept|reject|review","reason":"...","confidence":"high|medium|low"}]}
"""


class BaseClassifier:
    provider_name = "base"

    def is_ready(self) -> bool:
        return False

    def classify(self, candidates: List[Candidate]) -> List[Decision]:
        raise NotImplementedError


class UnavailableClassifier(BaseClassifier):
    provider_name = "unavailable"

    def classify(self, candidates: List[Candidate]) -> List[Decision]:
        return [
            Decision(
                candidate_id=item.candidate_id,
                verdict="review",
                provider=self.provider_name,
                reason="No semantic classifier provider is configured yet.",
                confidence="low",
            )
            for item in candidates
        ]


class FallbackClassifier(BaseClassifier):
    provider_name = "fallback"

    def __init__(self, primary: BaseClassifier, secondary: BaseClassifier) -> None:
        self.primary = primary
        self.secondary = secondary
        self.provider_name = f"{primary.provider_name}_with_fallback"

    def is_ready(self) -> bool:
        return self.primary.is_ready() or self.secondary.is_ready()

    def classify(self, candidates: List[Candidate]) -> List[Decision]:
        last_error: Exception | None = None

        if self.primary.is_ready():
            try:
                return self.primary.classify(candidates)
            except Exception as exc:
                last_error = exc

        if self.secondary.is_ready():
            try:
                decisions = self.secondary.classify(candidates)
                for decision in decisions:
                    if decision.provider == self.secondary.provider_name:
                        decision.provider = f"{self.secondary.provider_name}_fallback"
                return decisions
            except Exception as exc:
                last_error = exc

        if last_error:
            raise last_error
        raise RuntimeError("No semantic classifier provider is configured yet.")


class OpenAICompatibleClassifier(BaseClassifier):
    provider_name = "openai_compatible"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        batch_size: int = 3,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.batch_size = max(1, batch_size)
        self.max_retries = max(0, max_retries)

    def is_ready(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def classify(self, candidates: List[Candidate]) -> List[Decision]:
        decisions = []
        for start in range(0, len(candidates), self.batch_size):
            batch = candidates[start : start + self.batch_size]
            results = self._classify_batch(batch)
            for row in results:
                decisions.append(
                    Decision(
                        candidate_id=row.get("candidate_id", ""),
                        verdict=row.get("verdict", "review"),
                        provider=self.provider_name,
                        reason=row.get("reason", ""),
                        confidence=row.get("confidence", "unknown"),
                    )
                )
        return decisions

    def _classify_batch(self, candidates: List[Candidate]) -> list[dict]:
        user_payload = {
            "items": [
                {
                    "candidate_id": item.candidate_id,
                    "source_name": item.source_name,
                    "board": item.board,
                    "channel": item.channel,
                    "finance_scope": item.metadata.get("finance_scope", ""),
                    "source_notes": item.metadata.get("source_notes", ""),
                    "title": item.title,
                    "snippet": item.snippet,
                    "url": item.url,
                }
                for item in candidates
            ]
        }

        body = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, ensure_ascii=False),
                    },
                ],
            }
        ).encode("utf-8")

        for attempt in range(self.max_retries + 1):
            request = urllib.request.Request(
                self.base_url + "/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                content = payload["choices"][0]["message"]["content"]
                if isinstance(content, list):
                    text = "".join(
                        part.get("text", "") for part in content if isinstance(part, dict)
                    )
                else:
                    text = str(content)
                parsed = _extract_json_payload(text)
                return parsed.get("results", [])
            except urllib.error.HTTPError as exc:
                detail = ""
                try:
                    raw = exc.read().decode("utf-8", errors="replace")
                    detail = _extract_http_error_detail(raw)
                except Exception:
                    detail = ""
                if exc.code == 429 and attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                message = f"HTTP Error {exc.code}: {exc.reason}"
                if detail:
                    message = f"{message} | {detail}"
                raise RuntimeError(message) from exc
            except Exception as exc:
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                raise RuntimeError(str(exc)) from exc


def _extract_json_payload(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def _extract_http_error_detail(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                parts = [
                    str(error.get("message", "")).strip(),
                    str(error.get("type", "")).strip(),
                    str(error.get("code", "")).strip(),
                ]
                return " | ".join(part for part in parts if part)
            parts = [
                str(payload.get("message", "")).strip(),
                str(payload.get("msg", "")).strip(),
                str(payload.get("code", "")).strip(),
            ]
            detail = " | ".join(part for part in parts if part)
            if detail:
                return detail
    except json.JSONDecodeError:
        pass
    return re.sub(r"\s+", " ", text)[:400]


def build_classifier() -> BaseClassifier:
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    batch_size = int(os.environ.get("OPENAI_BATCH_SIZE", "3") or "3")
    max_retries = int(os.environ.get("OPENAI_MAX_RETRIES", "3") or "3")
    primary = None
    if api_key:
        primary = OpenAICompatibleClassifier(
            api_key=api_key,
            base_url=base_url,
            model=model,
            batch_size=batch_size,
            max_retries=max_retries,
        )

    fallback_api_key = os.environ.get("FALLBACK_OPENAI_API_KEY", "")
    fallback_base_url = os.environ.get("FALLBACK_OPENAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    fallback_model = os.environ.get("FALLBACK_OPENAI_MODEL", "")
    fallback_batch_size = int(os.environ.get("FALLBACK_OPENAI_BATCH_SIZE", str(batch_size)) or str(batch_size))
    fallback_max_retries = int(
        os.environ.get("FALLBACK_OPENAI_MAX_RETRIES", str(max_retries)) or str(max_retries)
    )

    secondary = None
    if fallback_api_key and fallback_model:
        secondary = OpenAICompatibleClassifier(
            api_key=fallback_api_key,
            base_url=fallback_base_url,
            model=fallback_model,
            batch_size=fallback_batch_size,
            max_retries=fallback_max_retries,
        )
        secondary.provider_name = "openai_compatible_glm"

    if primary and secondary:
        return FallbackClassifier(primary=primary, secondary=secondary)
    if primary:
        return primary
    if secondary:
        return secondary
    return UnavailableClassifier()
