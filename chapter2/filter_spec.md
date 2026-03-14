# Chapter 2 Filter Specification

This project does not use keywords as the main gate.

The filter is designed as a semantic classifier that answers one question:

`Is this item meaningfully about the intersection of AI and the financial industry?`

## Why not keywords

Keywords are too brittle.

They fail on cases like:

- company names such as `Morgan Stanley`, `BBVA`, `DBS`, `Adyen`, `Plaid`
- content where finance is implied by the institution rather than stated explicitly
- content where AI is described through product names, not generic terms

So the filter should reason over meaning, not literal token hits.

## Filter Position in the Pipeline

The filter runs during acquisition, not only after storage.

The acquisition flow is:

1. source adapter fetches the cheapest available candidate list
2. relevance classifier evaluates each candidate from title, snippet, source name, channel, and URL
3. candidates are split into:
   - `accepted`
   - `rejected`
   - `review`
4. only accepted items should move into later heavy processing stages such as full article parsing, transcript download, or summarization

## Candidate Input

Each candidate passed into the classifier contains:

- `source_name`
- `board`
- `channel`
- `finance_scope`
- `source_notes`
- `title`
- `snippet`
- `url`

This keeps the first pass cheap.

There is also a structural gate before semantic classification.

It rejects obvious junk such as:

- listing page self-links
- category and tag URLs
- generic calls to action such as `Read the story`
- titles that are too weak to represent a real publishable item

This is not the main relevance filter. It is a cheap hygiene layer that keeps the semantic classifier focused on real candidates.

## Output Schema

Each classifier decision returns:

- `candidate_id`
- `verdict`
  - `accept`
  - `reject`
  - `review`
- `reason`
- `confidence`

## Current Engineering Status

Implemented:

- unified relevance pipeline
- provider abstraction
- fallback state when no semantic provider is configured
- `accepted / rejected / review` buckets in every fetch output
- provider readiness command
- reclassification command for existing fetched outputs

Not live yet:

- a configured semantic model provider

Current environment status:

- no `OPENAI_API_KEY`
- no `OPENAI_BASE_URL`
- no `OPENAI_MODEL`

So the current pipeline is correctly wired, but all new items are routed to `review` until a provider is configured.

This is intentional. It is safer than pretending the items were semantically filtered when they were not.

## Provider Plan

Primary plan:

- use an OpenAI-compatible chat completion endpoint
- classify batches of candidates
- keep temperature at `0`
- require JSON output

This keeps the filter simple and inspectable.

## Operational Commands

Check provider readiness:

```bash
PYTHONPATH=src python -m finance_ai_news.filter_readiness
```

Reclassify existing Chapter 1 outputs after the provider is configured:

```bash
PYTHONPATH=src python -m finance_ai_news.reclassify_outputs
```
