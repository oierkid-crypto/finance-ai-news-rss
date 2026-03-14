# AI x Finance RSS

This repository now contains the Chapter 1 ingestion foundation.

The goal is not to crawl everything at once. The goal is to prove that each source family has a stable adapter path.

## Project Structure

- `chapter1/day1_sources.json`
  A machine-readable source wishlist for Day 1.
- `chapter1/source_manifest.json`
  Channel-level feasibility judgment.
- `chapter1/verification_report.md`
  Human-readable Chapter 1 conclusion.
- `src/finance_ai_news/`
  Minimal adapter and smoke test code.
- `.env`
  Local runtime configuration for model provider and source adapters.
- `web/`
  Static frontend for the product UI.

## Why this structure

Think of the agent like an editor running a newsroom:

- One reporter is good at websites and blogs.
- One reporter is good at `X`.
- One reporter is good at `YouTube`.
- One reporter is good at `Bilibili`.

If one reporter fails, the whole newsroom should not fail.

That is why the code is split into adapters. Each adapter handles one source family and its failure mode.

## Run the smoke test

Use Python module mode:

```bash
PYTHONPATH=src python -m finance_ai_news.smoke_test
```

This runs a `dry-run` smoke test for only `P0` sources.

To test every listed source:

```bash
PYTHONPATH=src python -m finance_ai_news.smoke_test --all
```

To attempt safe live reachability checks for website and feed adapters:

```bash
PYTHONPATH=src python -m finance_ai_news.smoke_test --mode live
```

The output report is written to:

```text
chapter1/output/smoke_test_report.json
```

## Run the Product

Start the local application:

```bash
PYTHONPATH=src uvicorn finance_ai_news.app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Main product endpoints:

- `/`
  Product UI
- `/api/dashboard`
  Unified product JSON
- `/feeds/direct_rss.xml`
  Direct RSS board feed
- `/feeds/fast_news_and_leaks.xml`
  Fast News board feed
- `/feeds/long_form.xml`
  Long Form board feed

To refresh the full pipeline manually:

```bash
PYTHONPATH=src python -m finance_ai_news.refresh_all
```

## Export a GitHub Pages build

The static export path turns the live dashboard state into:

- `docs/index.html`
- `docs/assets/*`
- `docs/data/dashboard.json`
- `docs/feeds/*.xml`

Run:

```bash
PYTHONPATH=src python -m finance_ai_news.export_static_site --output docs
```

Optional:

```env
PUBLIC_BASE_URL=https://<your-github-pages-url>
PAGES_CNAME=<your-custom-domain>
```

Why this exists:

- local FastAPI is the newsroom control room
- `export_static_site` is the publisher
- GitHub Pages is the printing press

The front-end automatically falls back to `data/dashboard.json` when the site is served statically, so the same UI works both locally and on GitHub Pages.

## GitHub Pages deployment

This repository includes:

- `.github/workflows/pages.yml`

The workflow does **not** run live fetchers in GitHub Actions, because your `X` cookies and model credentials are local operational assets.

The intended production flow is:

1. run the fetchers locally
2. review the published items
3. export `docs/`
4. push to GitHub
5. let GitHub Pages publish the static snapshot

## Important limitation

`dry-run` means:

- validate manifest completeness
- validate adapter prerequisites
- validate fallback design

It does **not** mean that every remote source has been fetched successfully.

That stricter test belongs in the next step, when we start wiring real fetchers and running live source-by-source checks.

## X Setup

The `X` pipeline is designed to reuse your old working environment instead of forcing a fresh install.

Default runtime resolution:

1. If `X_PYTHON_BIN` is set, use that interpreter.
2. Otherwise, reuse:
   `/Users/shaohua/Documents/AI/NewsFeed for Early Adopters/backend/venv/bin/python`
3. Otherwise, fall back to the current Python interpreter.

Default cookies resolution:

1. If `X_COOKIES_FILE` is set, use that file.
2. Otherwise, use `data/cookies.json` in this repo if it exists.
3. Otherwise, reuse:
   `/Users/shaohua/Documents/AI/NewsFeed for Early Adopters/backend/data/cookies.json`

The project automatically loads `.env` from the repository root, so you do not need to manually export these variables before every command.

To fetch the current `X` sources:

```bash
PYTHONPATH=src python -m finance_ai_news.fetch_x
```

The output report is written to:

```text
chapter1/output/x_latest.json
```

## Website and feed fetch

To fetch the current HTML and feed-based Day 1 sources:

```bash
PYTHONPATH=src python -m finance_ai_news.fetch_web
```

The output report is written to:

```text
chapter1/output/web_latest.json
```

## YouTube fetch

To fetch the current YouTube sources:

```bash
PYTHONPATH=src python -m finance_ai_news.fetch_youtube
```

The output report is written to:

```text
chapter1/output/youtube_latest.json
```

## Bilibili fetch

To fetch the current Bilibili sources:

```bash
PYTHONPATH=src python -m finance_ai_news.fetch_bilibili
```

The output report is written to:

```text
chapter1/output/bilibili_latest.json
```

## LinkedIn pilot readiness

`LinkedIn` is treated as a pilot channel, not a Day 1 core ingestion channel.

To check whether the local environment is ready for browser-based LinkedIn fetching:

```bash
PYTHONPATH=src python -m finance_ai_news.fetch_linkedin
```

The output report is written to:

```text
chapter1/output/linkedin_readiness.json
```

## Relevance Filter

The acquisition pipeline now includes a relevance filter stage.

This is not a keyword gate. It is engineered as a semantic classifier interface.

Current behavior:

- if a semantic model provider is configured, items can be classified into `accepted`, `rejected`, or `review`
- if no provider is configured, items are still fetched but routed into the `review` bucket

This keeps the pipeline honest: acquisition already includes the filter stage, but the current environment is not pretending to have live semantic decisions when no provider exists.

Chapter 2 documents live here:

- `chapter2/filter_spec.md`
- `chapter2/provider_config.example.json`

To run the semantic filter with Kimi later, fill in `.env` first.

Recommended Moonshot setup:

```env
OPENAI_API_KEY=your_moonshot_key
OPENAI_BASE_URL=https://api.moonshot.cn/v1
OPENAI_MODEL=kimi-k2-thinking
OPENAI_BATCH_SIZE=1
OPENAI_MAX_RETRIES=5
```

Notes:

- `OPENAI_API_KEY` is the variable name used by this codebase, but the value should be your `Moonshot / Kimi` API key.
- Do not prefix the key with `Bearer`.
- If Moonshot changes the exact model id shown in the console, update `OPENAI_MODEL` to match the console value.
- The previous placeholder `moonshot/kimi-k2.5` is not the current official model name shown in Moonshot's recent public docs.
- `OPENAI_BATCH_SIZE` and `OPENAI_MAX_RETRIES` help smooth out `429 engine_overloaded_error` responses from Moonshot.

Optional fallback setup with Zhipu GLM:

```env
FALLBACK_OPENAI_API_KEY=your_zhipu_key
FALLBACK_OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
FALLBACK_OPENAI_MODEL=glm-4.7
FALLBACK_OPENAI_BATCH_SIZE=1
FALLBACK_OPENAI_MAX_RETRIES=3
```

Notes:

- The fallback path uses the same OpenAI-compatible `/chat/completions` interface.
- In this codebase, the fallback provider is only used when the primary provider call fails.

Check whether the semantic filter provider is ready:

```bash
PYTHONPATH=src python -m finance_ai_news.filter_readiness
```

Run a direct provider probe:

```bash
PYTHONPATH=src python -m finance_ai_news.provider_probe
```

After you add the Kimi key, you can re-run semantic filtering on already-fetched Chapter 1 outputs:

```bash
PYTHONPATH=src python -m finance_ai_news.reclassify_outputs
```

## Current Product State

Working now:

- live `X` ingestion
- live website and feed ingestion
- RSS XML output per board
- complete frontend shell
- semantic filter pipeline wired into acquisition

Known gaps:

- the semantic provider is not live until you add the Kimi API key
- some individual sources still return `403`
- LinkedIn is intentionally still a pilot channel
