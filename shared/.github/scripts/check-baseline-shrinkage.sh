#!/usr/bin/env bash
# Ratchet gate: the baseline violation total may shrink or stay flat, never grow.
# Opt out for unrelated PRs with [skip-ratchet] in the PR title or body.
set -euo pipefail

BASELINE="packages/eslint-plugin/src/baselines/raw-db-from.json"

if echo "${PR_TITLE:-} ${PR_BODY:-}" | grep -q '\[skip-ratchet\]'; then
  echo "[skip-ratchet] present — ratchet gate bypassed"
  exit 0
fi

count() {
  node -e "let b={};try{b=require('$1')}catch{};let t=0;for(const k in b)t+=b[k];console.log(t)" 2>/dev/null || echo 0
}

if [ ! -f "$BASELINE" ]; then
  echo "FAIL: baseline missing at $BASELINE (fail-closed)"
  exit 1
fi

PR_TOTAL=$(count "./$BASELINE")

git fetch origin main --depth=1 >/dev/null 2>&1 || true
if git show origin/main:"$BASELINE" > /tmp/main-baseline.json 2>/dev/null; then
  MAIN_TOTAL=$(count /tmp/main-baseline.json)
else
  MAIN_TOTAL=$PR_TOTAL # first run / no main baseline yet
fi

echo "baseline total: main=$MAIN_TOTAL  pr=$PR_TOTAL"

if [ "$PR_TOTAL" -gt "$MAIN_TOTAL" ]; then
  echo "FAIL: baseline grew ($MAIN_TOTAL -> $PR_TOTAL)."
  echo "Fix the new violations, or add [skip-ratchet] if this PR is unrelated."
  exit 1
fi

echo "OK: baseline did not grow"
