#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH=src

echo "[1/3] Exporting static site to docs/"
python -m finance_ai_news.export_static_site --output docs

if [[ ! -d .git ]]; then
  echo "[2/3] Initializing a standalone git repository in this project"
  git init
  git branch -M main
fi

echo "[2/3] Staging changes"
git add .

if git diff --cached --quiet; then
  echo "No staged changes. Static site is already up to date."
else
  echo "[3/3] Creating commit"
  git commit -m "Publish latest AI x Finance snapshot"
fi

cat <<'EOF'

Local publication package is ready.

Next internet-facing step:
1. authenticate GitHub: gh auth login
2. create or connect a repo:
   gh repo create <repo-name> --public --source=. --remote=origin --push
   or
   git remote add origin <your-repo-url>
   git push -u origin main
3. enable GitHub Pages for the repo if needed

The workflow file .github/workflows/pages.yml will deploy docs/ to GitHub Pages on push to main.
EOF
