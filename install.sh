#!/usr/bin/env bash
# build-hardening-kit installer.
# Copies a hardening variant into a target repo, wires hooks, prints next steps.
#
# Usage:
#   ./install.sh <ts|js|go|python|polyglot> [target-dir]
#
#   target-dir defaults to the current directory.
#   Existing files are NOT overwritten unless you pass FORCE=1.
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARIANT="${1:-}"
TARGET="${2:-$(pwd)}"
FORCE="${FORCE:-0}"

if [ -z "$VARIANT" ]; then
  echo "usage: install.sh <ts|js|go|python|polyglot> [target-dir]" >&2
  exit 2
fi
if [ ! -d "$TARGET" ]; then
  echo "target dir not found: $TARGET" >&2
  exit 2
fi

yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
green() { printf "\033[32m%s\033[0m\n" "$1"; }

# copy SRC -> DST (relative to TARGET). Skip if exists unless FORCE=1.
copy() {
  local src="$1" dst="$TARGET/$2"
  if [ -e "$dst" ] && [ "$FORCE" != "1" ]; then
    yellow "skip (exists): $2   [FORCE=1 to overwrite]"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  cp -R "$src" "$dst"
  green "copied: $2"
}

install_shared_node() {
  copy "$KIT/shared/.prettierrc.json" ".prettierrc.json"
  copy "$KIT/shared/.prettierignore" ".prettierignore"
  copy "$KIT/shared/.husky" ".husky"
  copy "$KIT/shared/.github/workflows/ci.yml" ".github/workflows/ci.yml"
  copy "$KIT/shared/.github/scripts/check-env-schema.sh" ".github/scripts/check-env-schema.sh"
  copy "$KIT/shared/.github/scripts/check-baseline-shrinkage.sh" ".github/scripts/check-baseline-shrinkage.sh"
  copy "$KIT/shared/eslint-plugin-template" "packages/eslint-plugin"
  chmod +x "$TARGET/.husky/pre-commit" "$TARGET/.github/scripts/"*.sh 2>/dev/null || true
}

case "$VARIANT" in
  ts)
    install_shared_node
    copy "$KIT/ts/eslint.config.mjs" "eslint.config.mjs"
    copy "$KIT/ts/tsconfig.json" "tsconfig.json"
    copy "$KIT/ts/package.snippet.json" "package.snippet.json"
    NEXT='Merge package.snippet.json into package.json, then: npm install && npm run baseline:generate && npm run lint && npm run typecheck'
    ;;
  js)
    install_shared_node
    copy "$KIT/js/eslint.config.mjs" "eslint.config.mjs"
    copy "$KIT/js/jsconfig.json" "jsconfig.json"
    copy "$KIT/js/package.snippet.json" "package.snippet.json"
    NEXT='Merge package.snippet.json into package.json, then: npm install && npm run baseline:generate && npm run lint && npm run typecheck'
    ;;
  go)
    copy "$KIT/go/.golangci.yml" ".golangci.yml"
    copy "$KIT/go/rules.go" "rules.go"
    copy "$KIT/go/ci.snippet.yml" ".github/ci.go.snippet.yml"
    copy "$KIT/polyglot/.pre-commit-config.yaml" ".pre-commit-config.yaml"
    copy "$KIT/polyglot/semgrep" "semgrep"
    copy "$KIT/polyglot/.gitleaks.toml" ".gitleaks.toml"
    NEXT='Set your module path in .golangci.yml (prefix(...)). Then: pre-commit install && golangci-lint run'
    ;;
  python)
    copy "$KIT/python/pyproject.snippet.toml" "pyproject.snippet.toml"
    copy "$KIT/python/ci.snippet.yml" ".github/ci.python.snippet.yml"
    copy "$KIT/polyglot/.pre-commit-config.yaml" ".pre-commit-config.yaml"
    copy "$KIT/polyglot/semgrep" "semgrep"
    copy "$KIT/polyglot/.gitleaks.toml" ".gitleaks.toml"
    NEXT='Merge pyproject.snippet.toml into pyproject.toml. Then: pipx install pre-commit && pre-commit install && ruff check . && mypy .'
    ;;
  polyglot)
    copy "$KIT/polyglot/.pre-commit-config.yaml" ".pre-commit-config.yaml"
    copy "$KIT/polyglot/semgrep" "semgrep"
    copy "$KIT/polyglot/.gitleaks.toml" ".gitleaks.toml"
    copy "$KIT/polyglot/ci.yml" ".github/workflows/ci.yml"
    NEXT='pipx install pre-commit && pre-commit install && pre-commit run --all-files. Paste per-lang jobs from go/python ci.snippet.yml into .github/workflows/ci.yml'
    ;;
  *)
    echo "unknown variant: $VARIANT (use ts|js|go|python|polyglot)" >&2
    exit 2
    ;;
esac

echo
green "== $VARIANT hardening installed into $TARGET =="
echo
yellow "DAL policy: raw DB queries are blocked outside dal/ — see DAL_POLICY.md."
echo "Next: $NEXT"
