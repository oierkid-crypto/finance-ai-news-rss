from __future__ import annotations

import re
from typing import Callable, Iterable, List

from finance_ai_news.models import Source
from finance_ai_news.relevance.models import Candidate, Decision, FilteredBatch
from finance_ai_news.relevance.provider import build_classifier


GENERIC_TITLE_PATTERNS = {
    "read the story",
    "view",
    "watch now",
    "learn more",
    "financial services",
    "artificial intelligence",
    "customer solutions",
}

GENERIC_TITLE_PREFIXES = (
    "overview ",
    "overview:",
)

GENERIC_URL_PATTERNS = (
    "/category/",
    "/tag/",
    "/topics/",
    "/products/",
    "/solutions/",
)


def _looks_like_index_url(url: str) -> bool:
    for pattern in GENERIC_URL_PATTERNS:
        if pattern not in url:
            continue
        suffix = url.split(pattern, 1)[1].strip("/")
        if not suffix:
            return True
        # Some publishers, such as Google Cloud, place article slugs under
        # category-like segments (`/topics/financial-services/article-slug`).
        # Treat only shallow URLs as index pages and allow deeper article paths.
        if "/" not in suffix:
            return True
    return False


def build_candidate(
    source: Source,
    item: dict,
    index: int,
    title_getter: Callable[[dict], str],
    snippet_getter: Callable[[dict], str],
    url_getter: Callable[[dict], str],
) -> Candidate:
    return Candidate(
        candidate_id=f"{source.id}:{index}",
        source_id=source.id,
        source_name=source.name,
        board=source.board,
        channel=source.channel,
        title=(title_getter(item) or "").strip(),
        snippet=(snippet_getter(item) or "").strip(),
        url=(url_getter(item) or "").strip(),
        metadata={
            "region": source.region,
            "importance": source.importance,
            "finance_scope": source.finance_scope,
            "source_notes": source.notes,
        },
    )


def _structural_reject_reason(source: Source, candidate: Candidate) -> str | None:
    lowered_title = candidate.title.strip().lower()
    lowered_url = candidate.url.strip().lower()
    primary_url = (source.primary_url or "").rstrip("/").lower()
    fallback_url = (source.fallback_url or "").rstrip("/").lower()

    if not lowered_title or len(lowered_title) < 8:
        return "Candidate title is too weak to classify as a publishable item."
    if lowered_title in GENERIC_TITLE_PATTERNS:
        return "Candidate looks like a generic call-to-action instead of a real item."
    if any(lowered_title.startswith(prefix) for prefix in GENERIC_TITLE_PREFIXES):
        return "Candidate title looks like a product or navigation summary, not an article."
    if _looks_like_index_url(lowered_url):
        return "Candidate URL points to a category or product index rather than a specific item."
    if lowered_url and lowered_url.rstrip("/") in {primary_url, fallback_url}:
        return "Candidate points back to the listing page instead of a distinct item."
    if re.fullmatch(r"[A-Za-z0-9 .,&:+-]{1,32}", candidate.title) and not re.search(
        r"\b(ai|agent|agents|llm|model|bank|payment|payments|insurance|finance|financial)\b",
        lowered_title,
    ):
        return "Candidate title is too generic and lacks enough context for editorial use."
    return None


def apply_relevance_filter(
    source: Source,
    raw_items: List[dict],
    title_getter: Callable[[dict], str],
    snippet_getter: Callable[[dict], str],
    url_getter: Callable[[dict], str],
) -> FilteredBatch:
    classifier = build_classifier()
    provider_name = classifier.provider_name
    provider_ready = classifier.is_ready()
    candidates = [
        build_candidate(source, item, index, title_getter, snippet_getter, url_getter)
        for index, item in enumerate(raw_items)
    ]
    structural_rejections = []
    eligible_candidates = []
    for candidate in candidates:
        reject_reason = _structural_reject_reason(source, candidate)
        if reject_reason:
            structural_rejections.append(
                Decision(
                    candidate_id=candidate.candidate_id,
                    verdict="reject",
                    provider="structural_gate",
                    reason=reject_reason,
                    confidence="high",
                )
            )
        else:
            eligible_candidates.append(candidate)

    try:
        decisions = structural_rejections + classifier.classify(eligible_candidates)
    except Exception as exc:
        provider_name = f"{classifier.provider_name}_error"
        provider_ready = False
        decisions = [
            Decision(
                candidate_id=item.candidate_id,
                verdict="review",
                provider=provider_name,
                reason=f"Semantic provider failed at fetch time: {exc}",
                confidence="low",
            )
            for item in eligible_candidates
        ]
        decisions.extend(structural_rejections)
    decision_map = {decision.candidate_id: decision for decision in decisions}

    accepted_items = []
    rejected_items = []
    review_items = []
    for candidate, item in zip(candidates, raw_items):
        decision = decision_map.get(candidate.candidate_id)
        enriched = dict(item)
        enriched["source_finance_scope"] = source.finance_scope
        enriched["source_notes"] = source.notes
        enriched["filter_decision"] = decision.to_dict() if decision else None
        if not decision or decision.verdict == "review":
            review_items.append(enriched)
        elif decision.verdict == "accept":
            accepted_items.append(enriched)
        else:
            rejected_items.append(enriched)

    return FilteredBatch(
        provider=provider_name,
        provider_ready=provider_ready,
        accepted_items=accepted_items,
        rejected_items=rejected_items,
        review_items=review_items,
        decisions=decisions,
    )
