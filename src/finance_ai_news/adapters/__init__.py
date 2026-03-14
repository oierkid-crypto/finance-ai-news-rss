from finance_ai_news.adapters.base import BaseAdapter
from finance_ai_news.adapters.bilibili import BilibiliAdapter
from finance_ai_news.adapters.feed import FeedAdapter
from finance_ai_news.adapters.html import HtmlAdapter
from finance_ai_news.adapters.x_account import XAccountAdapter
from finance_ai_news.adapters.youtube import YouTubeAdapter

ADAPTERS = {
    "html": HtmlAdapter,
    "feed": FeedAdapter,
    "youtube": YouTubeAdapter,
    "x_account": XAccountAdapter,
    "bilibili": BilibiliAdapter,
}
