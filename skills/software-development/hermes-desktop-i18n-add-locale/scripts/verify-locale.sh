#!/usr/bin/env bash
# verify-locale.sh — checks a generated Hermes Desktop locale file is COMPLETE and valid.
#
# Usage:
#   bash scripts/verify-locale.sh <locale-code> [repo-root]
#
# Examples:
#   bash scripts/verify-locale.sh es
#   bash scripts/verify-locale.sh fr /home/migbert/.hermes/hermes-agent
#
# Exit codes:
#   0 = all checks passed
#   1 = one or more checks failed (details printed to stderr)
#
# What it checks:
#   1. File exists at apps/desktop/src/i18n/<locale>.ts
#   2. Curly braces balanced (open == close)
#   3. File ends with `})` (closes defineLocale + object)
#   4. Contains the defineLocale() wrapper call
#   5. All expected top-level sections present (no missing, no duplicates)
#   6. Compiled build (if release dir present) contains at least one known string
#
# This is the post-delegation gate: a subagent that "finished" may have
# truncated the file mid-section. ALWAYS run this after any delegate_task
# that generated or completed a locale file.

set -u

LOCALE="${1:-}"
REPO="${2:-$HOME/.hermes/hermes-agent}"

if [[ -z "$LOCALE" ]]; then
  echo "ERROR: missing locale code. Usage: verify-locale.sh <locale> [repo-root]" >&2
  exit 1
fi

FILE="$REPO/apps/desktop/src/i18n/$LOCALE.ts"
FAIL=0

# Expected top-level sections in en.ts (the canonical ordering/set).
SECTIONS="common fileMenu boot notifications remoteDisplayBanner titlebar keybinds language settings skills starmap agents commandCenter messaging profiles cron artifacts sidebar composer statusStack updates install onboarding modelPicker modelVisibility shell rightSidebar preview assistant prompts desktop errors ui"

echo "== Verifying locale: $LOCALE =="
echo "File: $FILE"

if [[ ! -f "$FILE" ]]; then
  echo "FAIL: file not found" >&2
  exit 1
fi

# 1. Brace balance
OPEN=$(grep -o '{' "$FILE" | wc -l)
CLOSE=$(grep -o '}' "$FILE" | wc -l)
if [[ "$OPEN" -eq "$CLOSE" ]]; then
  echo "OK   braces balanced ($OPEN open / $CLOSE close)"
else
  echo "FAIL braces unbalanced ($OPEN open / $CLOSE close)" >&2
  FAIL=1
fi

# 2. Ends with `})`
if tail -c 4 "$FILE" | grep -q '})'; then
  echo "OK   file ends with '})'"
else
  echo "FAIL file does not end with '})'" >&2
  FAIL=1
fi

# 3. defineLocale wrapper present
if grep -q 'defineLocale({' "$FILE"; then
  echo "OK   contains defineLocale({"
else
  echo "FAIL missing defineLocale({ wrapper" >&2
  FAIL=1
fi

# 4. Each expected section present exactly once at top level
for S in $SECTIONS; do
  COUNT=$(grep -cE "^  $S: \{" "$FILE")
  if [[ "$COUNT" -eq 1 ]]; then
    :
  else
    echo "FAIL section '$S' appears $COUNT time(s) (expected 1)" >&2
    FAIL=1
  fi
done
[[ $FAIL -eq 0 ]] && echo "OK   all $(echo $SECTIONS | wc -w) top-level sections present exactly once"

# 5. Compiled build string check (only if release dir exists)
RELEASE_JS=$(ls "$REPO"/apps/desktop/release/linux-unpacked/resources/app.asar.unpacked/dist/assets/index-*.js 2>/dev/null | head -1)
if [[ -n "$RELEASE_JS" ]]; then
  PROBE="Guardar"
  if [[ "$LOCALE" == "es" ]]; then PROBE="Guardar"; fi
  if grep -q "$PROBE" "$RELEASE_JS"; then
    echo "OK   compiled build contains probe string '$PROBE'"
  else
    echo "WARN compiled build does not contain '$PROBE' — rebuild may be needed (not fatal)" >&2
  fi
else
  echo "SKIP compiled-build check (release dir not found)"
fi

echo "----"
if [[ $FAIL -eq 0 ]]; then
  echo "RESULT: PASS — locale $LOCALE is complete and valid"
  exit 0
else
  echo "RESULT: FAIL — see errors above" >&2
  exit 1
fi
