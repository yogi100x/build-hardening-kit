#!/usr/bin/env bash
# Fail the build if an env var read in JS/TS source is missing from .env.example.
# Catches the "undefined in prod" class of bug at PR time.
# Reads: process.env.X, process.env["X"], process.env['X'], import.meta.env.X
# (Vite's built-ins MODE, DEV, PROD, SSR, BASE_URL are ignored).
# Not read: destructuring (const { X } = process.env) — list those by hand.
set -euo pipefail

EXAMPLE=".env.example"
if [ ! -f "$EXAMPLE" ]; then
  echo "no $EXAMPLE found — skipping env-schema check"
  exit 0
fi

# Accept `X=`, `export X=` and a bare `X` line.
declared=$(sed -nE 's/^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*).*/\2/p' "$EXAMPLE" | sort -u)

used=$(grep -rhoE \
  "process\.env\.[A-Za-z_][A-Za-z0-9_]*|process\.env\[[\"'][A-Za-z_][A-Za-z0-9_]*[\"']\]|import\.meta\.env\.[A-Za-z_][A-Za-z0-9_]*" \
  --include='*.js' --include='*.jsx' --include='*.mjs' --include='*.cjs' \
  --include='*.ts' --include='*.tsx' --include='*.mts' --include='*.cts' \
  --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=build --exclude-dir=.next \
  src apps packages 2>/dev/null \
  | sed -E "s/^process\.env\.//; s/^process\.env\[[\"']//; s/[\"']\]$//; s/^import\.meta\.env\.//" \
  | grep -vxE 'MODE|DEV|PROD|SSR|BASE_URL' | sort -u || true)

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
