from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from finance_ai_news.models import Source


@dataclass(frozen=True)
class BoardDefinition:
    slug: str
    section_id: str
    title: str
    subtitle: str
    description: str

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "section_id": self.section_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
        }


# Keep the legacy slugs stable so existing feed URLs do not break, but give them
# the new product meaning requested for the three visible columns.
BOARD_DEFINITIONS = {
    "direct_rss": BoardDefinition(
        slug="direct_rss",
        section_id="who_is_doing_what",
        title="FinAI 的最新动向",
        subtitle="Who is Doing What",
        description="关注全球 Finance x AI 项目、投资并购与组织人事变化，尤其追踪大型金融机构谁在做什么。",
    ),
    "fast_news_and_leaks": BoardDefinition(
        slug="fast_news_and_leaks",
        section_id="what_is_becoming_possible",
        title="FinAI 的技术与应用",
        subtitle="What is Becoming Possible",
        description="关注前沿 AI 技术与金融行业应用的结合，回答新的能力边界正在如何被打开。",
    ),
    "long_form": BoardDefinition(
        slug="long_form",
        section_id="what_could_slow_things_down",
        title="FinAI 的监管、合规与风险治理",
        subtitle="What Could Slow Things Down",
        description="关注监管、合规、模型风险与治理问题，判断哪些约束会拖慢落地速度。",
    ),
}

BOARD_ORDER = ["direct_rss", "fast_news_and_leaks", "long_form"]

SOURCE_REGION_OVERRIDES = {
    "google-cloud-financial-services": "美国",
    "aws-ml-blog-financial-services": "美国",
    "microsoft-financial-services-blog": "美国",
    "openai-customer-stories": "美国",
    "plaid-intelligent-finance": "美国",
    "openai-x": "美国",
    "anthropic-x": "美国",
    "ant-group-news": "中国",
    "qbitai": "中国",
    "jiqizhixin": "中国",
    "waic-bilibili": "中国",
    "evident-banking-brief": "欧洲",
    "finextra": "欧洲",
    "simon-taylor-x": "欧洲",
    "fintech-brainfood": "欧洲",
    "11fs-fintech-insider": "欧洲",
    "11fs-youtube": "欧洲",
}

SOURCE_INDUSTRY_OVERRIDES = {
    "evident-banking-brief": ["银行"],
}

REGION_KEYWORDS = {
    "中国": ["china", "chinese", "中国", "内地", "香港", "中信", "蚂蚁集团", "ant group"],
    "美国": ["united states", "u.s.", "us ", " usa", "america", "美国", "paypal", "openai", "anthropic", "plaid"],
    "欧洲": ["europe", "european", "uk", "united kingdom", "britain", "london", "eu ", "欧洲", "英国", "bbva", "11fs"],
    "亚洲其他": ["asia pacific", "apac", "singapore", "japan", "india", "middle east", "亚洲", "新加坡", "日本", "印度", "中东"],
}

INDUSTRY_KEYWORDS = {
    "银行": ["bank", "banking", "retail banking", "commercial banking", "银行"],
    "投行": ["investment bank", "investment banking", "capital markets", "投行", "投研"],
    "保险": ["insurance", "insurer", "underwriting", "claims", "保险"],
    "咨询": ["consulting", "consultancy", "advisor", "advisory", "咨询"],
    "审计": ["audit", "auditor", "assurance", "accounting firm", "审计"],
    "券商": ["broker", "brokerage", "securities firm", "dealer", "券商", "证券"],
    "公募": ["asset manager", "asset management", "mutual fund", "public fund", "公募", "资管"],
    "私募": ["private equity", "hedge fund", "private credit", "private fund", "私募"],
}

INSTITUTION_KEYWORDS = {
    "德勤": ["deloitte", "德勤"],
    "CITIC": ["citic", "中信"],
    "容诚": ["容诚"],
    "Google Cloud": ["google cloud"],
    "Google": [" google ", "google,"],
    "Microsoft": ["microsoft"],
    "OpenAI": ["openai"],
    "Anthropic": ["anthropic"],
    "Plaid": ["plaid"],
    "Ant Group": ["ant group", "蚂蚁集团"],
    "PayPal": ["paypal"],
    "CME Group": ["cme group"],
    "Evident": ["evident"],
    "BBVA": ["bbva"],
    "BNY": ["bny", "bank of new york mellon"],
    "Morgan Stanley": ["morgan stanley"],
    "Cognizant": ["cognizant"],
    "Ramp": ["ramp"],
    "11FS": ["11fs"],
    "Finextra": ["finextra"],
    "WAIC": ["waic", "世界人工智能大会"],
}

MOVEMENT_KEYWORDS = [
    ("launch", 2),
    ("launched", 2),
    ("rollout", 2),
    ("rolled out", 2),
    ("deployed", 2),
    ("deploying", 2),
    ("上线", 2),
    ("推出", 2),
    ("发布", 1),
    ("announced", 2),
    ("announcement", 2),
    ("partner", 2),
    ("partnership", 2),
    ("customer story", 2),
    ("case study", 2),
    ("appoint", 3),
    ("appointed", 3),
    ("hire", 2),
    ("hiring", 2),
    ("chief ai officer", 4),
    ("committee", 2),
    ("org chart", 3),
    ("organization", 1),
    ("investment", 3),
    ("invest", 3),
    ("funding", 3),
    ("acquisition", 4),
    ("acquire", 4),
    ("m&a", 4),
    ("jointly", 2),
    ("adoption", 2),
    ("implemented", 2),
]

TECH_KEYWORDS = [
    ("rag", 3),
    ("retrieval augmented", 3),
    ("long context", 3),
    ("copilot", 3),
    ("multi-agent", 4),
    ("multi agent", 4),
    ("agentic", 2),
    ("workflow", 2),
    ("multimodal", 3),
    ("ocr", 3),
    ("reasoning", 2),
    ("automation", 2),
    ("document processing", 3),
    ("search", 1),
    ("benchmark", 2),
    ("model", 1),
    ("生成式", 2),
    ("大模型", 2),
    ("多模态", 3),
    ("长上下文", 3),
    ("检索增强", 3),
    ("工作流", 2),
    ("助手", 2),
]

RISK_KEYWORDS = [
    ("governance", 4),
    ("regulation", 4),
    ("regulatory", 4),
    ("compliance", 4),
    ("risk", 2),
    ("model risk", 5),
    ("audit", 4),
    ("audit trail", 5),
    ("explainability", 5),
    ("privacy", 4),
    ("security", 3),
    ("responsible ai", 4),
    ("legal", 3),
    ("suitability", 5),
    ("private deployment", 4),
    ("permissions", 3),
    ("sensitive information", 4),
    ("third-party model risk", 5),
    ("监管", 5),
    ("合规", 5),
    ("风险", 3),
    ("治理", 4),
    ("审计", 4),
    ("留痕", 5),
    ("可解释", 5),
    ("权限", 3),
    ("私有化", 4),
    ("隔离", 4),
    ("敏感信息", 4),
    ("责任归属", 5),
]


def get_board_definition(board_slug: str) -> BoardDefinition:
    return BOARD_DEFINITIONS.get(board_slug, BOARD_DEFINITIONS["direct_rss"])


def _normalize_text(parts: Iterable[str]) -> str:
    return " ".join((part or "").strip() for part in parts if part).lower()


def _score_keywords(text: str, weighted_keywords: Iterable[tuple[str, int]]) -> int:
    score = 0
    for keyword, weight in weighted_keywords:
        if keyword in text:
            score += weight
    return score


def _collect_matches(text: str, mapping: dict[str, Iterable[str]]) -> List[str]:
    matches: List[str] = []
    for label, keywords in mapping.items():
        for keyword in keywords:
            if keyword in text:
                matches.append(label)
                break
    return matches


def _dedupe(values: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def infer_board(source: Source | None, title: str, snippet: str, url: str) -> str:
    text = _normalize_text([title, snippet, url, getattr(source, "notes", ""), getattr(source, "name", "")])
    movement_score = _score_keywords(text, MOVEMENT_KEYWORDS)
    tech_score = _score_keywords(text, TECH_KEYWORDS)
    risk_score = _score_keywords(text, RISK_KEYWORDS)

    if risk_score >= max(movement_score, tech_score) and risk_score >= 4:
        return "long_form"
    if movement_score >= tech_score and movement_score >= 2:
        return "direct_rss"
    if tech_score >= 2:
        return "fast_news_and_leaks"

    if source and source.channel in {"youtube", "podcast", "bilibili"}:
        return "fast_news_and_leaks"
    if source and source.channel == "x":
        return "direct_rss"
    return "direct_rss"


def infer_region_tags(source: Source | None, title: str, snippet: str, url: str) -> List[str]:
    text = _normalize_text([title, snippet, url, getattr(source, "name", "")])
    matches = _collect_matches(text, REGION_KEYWORDS)
    if matches:
        return [matches[0]]
    if source and source.id in SOURCE_REGION_OVERRIDES:
        return [SOURCE_REGION_OVERRIDES[source.id]]
    if source and source.region == "china":
        return ["中国"]
    return []


def infer_industry_tags(source: Source | None, title: str, snippet: str, url: str) -> List[str]:
    text = _normalize_text([title, snippet, url, getattr(source, "name", "")])
    tags = []
    if source:
        tags.extend(SOURCE_INDUSTRY_OVERRIDES.get(source.id, []))
    tags.extend(_collect_matches(text, INDUSTRY_KEYWORDS))
    return _dedupe(tags)


def infer_institution_tags(source: Source | None, title: str, snippet: str, url: str) -> List[str]:
    text = f" {_normalize_text([title, snippet, url, getattr(source, 'name', '')])} "
    tags = _collect_matches(text, INSTITUTION_KEYWORDS)
    if "Google Cloud" in tags and "Google" in tags:
        tags = [tag for tag in tags if tag != "Google"]
    return _dedupe(tags)[:3]


def classify_and_tag_item(source: Source | None, title: str, snippet: str, url: str) -> dict:
    board = infer_board(source=source, title=title, snippet=snippet, url=url)
    definition = get_board_definition(board)
    tags = {
        "region": infer_region_tags(source=source, title=title, snippet=snippet, url=url),
        "industry": infer_industry_tags(source=source, title=title, snippet=snippet, url=url),
        "institution": infer_institution_tags(source=source, title=title, snippet=snippet, url=url),
    }
    tags["all"] = _dedupe(tags["region"] + tags["industry"] + tags["institution"])
    return {
        "board": board,
        "section_id": definition.section_id,
        "section_title": definition.title,
        "section_subtitle": definition.subtitle,
        "section_description": definition.description,
        "tags": tags,
    }
