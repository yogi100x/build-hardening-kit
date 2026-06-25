#!/usr/bin/env bash
# Fail the build if any process.env.X referenced in source is missing from .env.example.
# Catches the "undefined in prod" class of bug at PR time.
set -euo pipefail

EXAMPLE=".env.example"
if [ ! -f "$EXAMPLE" ]; then
  echo "no $EXAMPLE found — skipping env-schema check"
  exit 0
fi

declared=$(grep -oE '^[A-Z0-9_]+' "$EXAMPLE" | sort -u)
used=$(grep -rhoE 'process\.env\.[A-Z0-9_]+' src apps packages 2>/dev/null \
  | sed 's/process\.env\.//' | sort -u || true)

missing=""
for v in $used; do
  if ! echo "$declared" | grep -qx "$v"; then
    missing="$missing $v"
  fi
done

if [ -n "$missing" ]; then
  echo "FAIL: env vars used in code but absent from $EXAMPLE:$missing"
  echo "Add them to $EXAMPLE (value can be a placeholder)."
  exit 1
fi

echo "OK: every referenced env var is declared in $EXAMPLE"
