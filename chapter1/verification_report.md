# Chapter 1 Verification Report

As of 2026-03-12, this report answers one practical question:

Can the channels in the current source wishlist be acquired stably enough to support a paid `AI x Finance` information product?

The short answer is:

- `Yes` for website/blog/newsletter/podcast/YouTube/Bilibili.
- `Yes, with constraints` for `X`.
- `Partially` for `LinkedIn`.
- `Not stable enough for Day 1 core ingestion` for `WeChat public accounts`.

This matters because Chapter 1 is not just media research. It is source-system design. A source only counts if an agent can fetch it repeatedly with a known tool path.

## Stability Standard

For this project, a channel is marked `stable` only if it passes most of these checks:

1. It has a repeatable acquisition path.
2. It does not depend on a one-off manual copy step.
3. It can be refreshed by scheduler.
4. It has a fallback path when the main path fails.
5. Its anti-bot or login friction is acceptable for an internal product pipeline.

## Final Verdict by Channel

| Channel | Verdict | Why |
| --- | --- | --- |
| Website / blog / company news page | Pass | HTML parsing and custom RSS routes are mature and low-risk. |
| Newsletter | Pass | Many newsletters expose feed endpoints directly, especially Substack-style sites. |
| Podcast | Pass | Podcast RSS is one of the most stable feed formats on the internet. |
| YouTube | Pass | Main path is `yt-dlp`; fallback is native YouTube video feed. |
| Bilibili | Pass | RSSHub already supports user video routes; good enough for Day 1. |
| X | Pass with constraints | Best path is `twikit + cookies`. Stable enough for curated account lists, but not ideal for unbounded crawling. |
| LinkedIn company page | Conditional pass | Can be fetched with RSS-style adapters or browser automation, but stability is lower than X and YouTube. |
| LinkedIn personal posts | Partial pass | Technically fetchable with logged-in browser automation, but not stable enough to be a large-scale Day 1 core source. |
| WeChat public accounts | Fail for Day 1 core | High value, but access and automation stability are too inconsistent for the main ingestion layer. |

## Why the Verdict Changed After Reviewing the Old Project

The old project at [NewsFeed for Early Adopters](/Users/shaohua/Documents/AI/NewsFeed%20for%20Early%20Adopters) materially changes the feasibility judgment.

It already proves three important things:

1. `X` was not solved with vague scraping. It used `twikit + cookies + filters`.
2. `YouTube` was not solved with page scraping. It used `yt-dlp` for channel videos and transcript retrieval.
3. `YouTube` already had a fallback path using native video feeds when `yt-dlp` failed.

Relevant code:

- X fetcher: [x_fetcher.py](/Users/shaohua/Documents/AI/NewsFeed%20for%20Early%20Adopters/backend/api/services/x_fetcher.py)
- YouTube fetcher: [youtube_fetcher.py](/Users/shaohua/Documents/AI/NewsFeed%20for%20Early%20Adopters/backend/api/services/youtube_fetcher.py)
- Scheduler fallback logic: [refresh_scheduler.py](/Users/shaohua/Documents/AI/NewsFeed%20for%20Early%20Adopters/backend/scheduler/refresh_scheduler.py)

That means Chapter 1 is no longer just a hypothesis. For `X` and `YouTube`, there is already a validated adapter pattern.

## Channel-by-Channel Decision

### 1. Direct RSS Content

This bucket should hold content that users can open and read inside the product as the main high-signal flow.

Recommended Day 1 channels:

- Company blogs and industry blogs
- News and case-study pages
- Newsletters
- Podcasts
- Select industry media pages

Why this is stable:

- The fetch pattern is simple: `HTTP page -> parse list -> fetch detail -> store content`.
- If the site has feed output, use that. If not, make a custom route.
- No account login is required for most of these.

### 2. Fast News and Leaks

This bucket should hold short, high-signal snapshots from selected people and company accounts.

Recommended Day 1 channels:

- `X` selected accounts
- Limited `LinkedIn` company pages
- A very small number of `LinkedIn` personal accounts only if they prove very high value

Why `X` passes:

- Your old project already used `twikit` successfully.
- The fetch model fits the product: small whitelist, scheduled refresh, strong filters.
- This is much easier than trying to crawl the whole platform.

Why `LinkedIn` only partially passes:

- For company pages, there are workable adapter paths.
- For personal posts, a logged-in browser session is usually required.
- That creates more operational fragility than `X`.

So the right product decision is:

- `X`: Day 1 core for the `快讯 & Leaks` board
- `LinkedIn company`: small pilot
- `LinkedIn personal`: editor-only radar first, product surface later

### 3. Long-form Content

This bucket should hold title, summary, and external link only.

Recommended Day 1 channels:

- Podcasts
- YouTube
- Bilibili
- Research blogs
- Conference video archives

Why this is stable:

- Podcast feeds are already RSS-native.
- YouTube has both `yt-dlp` and feed fallback.
- Bilibili has RSSHub route support and stable creator-page structure.

This is operationally the easiest high-value board after `Direct RSS`.

## Day 1 Core Decision

These channels are strong enough to enter the first production version:

- Website / blog / company news pages
- Newsletter
- Podcast
- YouTube
- Bilibili
- X

These channels should be limited, not excluded:

- LinkedIn company pages
- LinkedIn personal posts

These channels should be delayed to Phase 2:

- WeChat public accounts

## Architecture Recommendation

The Chapter 1 pipeline should be designed as multiple specialized source adapters, not one giant crawler.

The simplest mental model is:

- `Adapter A`: websites, newsletters, podcasts
- `Adapter B`: X selected accounts
- `Adapter C`: YouTube and video transcript extraction
- `Adapter D`: Bilibili video feeds
- `Adapter E`: browser-automation fallback for LinkedIn
- `Adapter F`: experimental WeChat ingestion, isolated from the main pipeline

This matters because each source family has different failure modes. A good agent system isolates those modes instead of mixing them together.

## Evidence Used

Local engineering evidence:

- [README.md](/Users/shaohua/Documents/AI/NewsFeed%20for%20Early%20Adopters/README.md)
- [x_fetcher.py](/Users/shaohua/Documents/AI/NewsFeed%20for%20Early%20Adopters/backend/api/services/x_fetcher.py)
- [youtube_fetcher.py](/Users/shaohua/Documents/AI/NewsFeed%20for%20Early%20Adopters/backend/api/services/youtube_fetcher.py)
- [refresh_scheduler.py](/Users/shaohua/Documents/AI/NewsFeed%20for%20Early%20Adopters/backend/scheduler/refresh_scheduler.py)

Public documentation:

- RSSHub social-media routes: <https://docs.rsshub.app/zh/routes/social-media>
- RSSHub popular routes including Bilibili and YouTube: <https://docs.rsshub.app/zh/routes/popular>
- Twikit repository: <https://github.com/d60/twikit>
- yt-dlp repository: <https://github.com/yt-dlp/yt-dlp>
- Playwright authentication docs: <https://playwright.dev/docs/auth>
- WeWe RSS repository: <https://github.com/cooderl/wewe-rss>
- Wechat2RSS repository: <https://github.com/ttttmr/Wechat2RSS>

## Bottom Line

The Chapter 1 wishlist does not fully pass as one uniform group.

The accurate result is:

- `Core stable`: websites, newsletters, podcasts, YouTube, Bilibili, X
- `Pilot only`: LinkedIn
- `Phase 2 experimental`: WeChat public accounts

That is still a very strong result. It means the product can start with a stable and differentiated acquisition layer without waiting for the hardest Chinese-platform automation problem to be solved first.
