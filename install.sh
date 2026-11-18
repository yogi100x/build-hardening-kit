#!/usr/bin/env bash
# build-hardening-kit installer.
# Copies a hardening variant into a target repo, wires hooks, prints next steps.
#
# Usage:
#   ./install.sh <ts|js|go|python|polyglot|google> [target-dir]
#
#   target-dir defaults to the current directory.
#   `google` installs the governance layer (CODEOWNERS, Dependabot, CodeQL,
#   branch-protection + Google-grade docs) — layer it on top of a language variant.
#   Variants can be combined (e.g. ts then python): each stack gets its own
#   workflow file (.github/workflows/hardening-<stack>.yml), so none is skipped.
#   Existing files are NOT overwritten unless you pass FORCE=1.
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARIANT="${1:-}"
TARGET="${2:-$(pwd)}"
FORCE="${FORCE:-0}"
USAGE="usage: install.sh <ts|js|go|python|polyglot|google> [target-dir]"

if [ -z "$VARIANT" ]; then
  echo "$USAGE" >&2
  exit 2
fi
if [ ! -d "$TARGET" ]; then
  echo "target dir not found: $TARGET" >&2
  exit 2
fi

yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
green() { printf "\033[32m%s\033[0m\n" "$1"; }

# copy SRC -> DST (relative to TARGET). Skip if it exists unless FORCE=1.
# A directory replaces the old one (cp -R into an existing dir would nest it).
# Returns 0 when it copied, 1 when it skipped.
copy() {
  local src="$1" dst="$TARGET/$2"
  if [ -e "$dst" ]; then
    if [ "$FORCE" != "1" ]; then
      yellow "skip (exists): $2   [FORCE=1 to overwrite]"
      return 1
    fi
    rm -rf "$dst"
  fi
  mkdir -p "$(dirname "$dst")"
  cp -R "$src" "$dst"
  green "copied: $2"
  return 0
}

# copy an executable script and mark it executable only if it was copied.
copy_exec() {
  if copy "$1" "$2"; then chmod +x "$TARGET/$2"; fi
}

install_shared_node() {
  copy "$KIT/shared/.prettierrc.json" ".prettierrc.json" || true
  copy "$KIT/shared/.prettierignore" ".prettierignore" || true
  if copy "$KIT/shared/.husky" ".husky"; then chmod +x "$TARGET/.husky/pre-commit"; fi
  copy "$KIT/shared/.github/workflows/hardening-node.yml" ".github/workflows/hardening-node.yml" || true
  copy_exec "$KIT/shared/.github/scripts/check-env-schema.sh" ".github/scripts/check-env-schema.sh"
  copy_exec "$KIT/shared/.github/scripts/check-baseline-shrinkage.sh" ".github/scripts/check-baseline-shrinkage.sh"
  copy "$KIT/shared/eslint-plugin-template" "packages/eslint-plugin" || true
}

install_polyglot_common() {
  copy "$KIT/polyglot/.pre-commit-config.yaml" ".pre-commit-config.yaml" || true
  copy "$KIT/polyglot/semgrep" "semgrep" || true
  copy "$KIT/polyglot/.gitleaks.toml" ".gitleaks.toml" || true
  copy "$KIT/polyglot/hardening-polyglot.yml" ".github/workflows/hardening-polyglot.yml" || true
}

install_governance() {
  copy "$KIT/.github/CODEOWNERS" ".github/CODEOWNERS" || true
  copy "$KIT/.github/dependabot.yml" ".github/dependabot.yml" || true
  copy "$KIT/.github/workflows/codeql.yml" ".github/workflows/codeql.yml" || true
  copy "$KIT/docs/BRANCH_PROTECTION.md" "docs/BRANCH_PROTECTION.md" || true
  copy "$KIT/GOOGLE_GRADE.md" "GOOGLE_GRADE.md" || true
  copy "$KIT/DAL_POLICY.md" "DAL_POLICY.md" || true
}

PRE_COMMIT='pipx install pre-commit (or use: uvx pre-commit) && pre-commit install'

case "$VARIANT" in
  ts)
    install_shared_node
    copy "$KIT/ts/eslint.config.mjs" "eslint.config.mjs" || true
    copy "$KIT/ts/tsconfig.json" "tsconfig.json" || true
    copy "$KIT/ts/package.snippet.json" "package.snippet.json" || true
    NEXT='Merge package.snippet.json into package.json and delete it, then: npm install && npm run baseline:generate && npm run check && npm test'
    ;;
  js)
    install_shared_node
    copy "$KIT/js/eslint.config.mjs" "eslint.config.mjs" || true
    copy "$KIT/js/jsconfig.json" "jsconfig.json" || true
    copy "$KIT/js/package.snippet.json" "package.snippet.json" || true
    NEXT='Merge package.snippet.json into package.json and delete it, then: npm install && npm run baseline:generate && npm run check && npm test'
    ;;
  go)
    install_polyglot_common
    copy "$KIT/go/.golangci.yml" ".golangci.yml" || true
    copy "$KIT/go/rules.go" "rules.go" || true
    copy "$KIT/go/hardening-go.yml" ".github/workflows/hardening-go.yml" || true
    if [ -e "$TARGET/Makefile" ]; then
      copy "$KIT/go/Makefile.snippet" "Makefile.hardening" || true
      MAKE_NOTE='Merge Makefile.hardening into your Makefile and delete it.'
    else
      copy "$KIT/go/Makefile.snippet" "Makefile" || true
      MAKE_NOTE=''
    fi
    NEXT="Set your module path in .golangci.yml (gci prefix). Add the ruleguard DSL: go get github.com/quasilyte/go-ruleguard/dsl. $MAKE_NOTE Then: $PRE_COMMIT && make check"
    ;;
  python)
    install_polyglot_common
    copy "$KIT/python/pyproject.snippet.toml" "pyproject.snippet.toml" || true
    copy "$KIT/python/hardening-python.yml" ".github/workflows/hardening-python.yml" || true
    NEXT="Merge pyproject.snippet.toml into pyproject.toml and delete it. Add the tools: uv add --dev ruff mypy pytest. Then: $PRE_COMMIT && uv run ruff check . && uv run mypy ."
    ;;
  polyglot)
    install_polyglot_common
    NEXT="$PRE_COMMIT && pre-commit run --all-files. Add a language variant (go, python, ts, js) for its CI workflow."
    ;;
  google)
    install_governance
    NEXT='Edit .github/CODEOWNERS (it ships commented out: placeholder owners enforce nothing), then enforce: see docs/BRANCH_PROTECTION.md. Layer this on top of a language variant (run install.sh <ts|js|go|python|polyglot> too).'
    ;;
  *)
    echo "unknown variant: $VARIANT" >&2
    echo "$USAGE" >&2
    exit 2
    ;;
esac

echo
green "== $VARIANT hardening installed into $TARGET =="
echo
yellow "DAL policy: raw DB queries are blocked outside dal/ — see DAL_POLICY.md."
echo "Next: $NEXT"
