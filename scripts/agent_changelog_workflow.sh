#!/usr/bin/env bash
# Shield — agent / developer workflow: changelog + version.properties
# Cursor: see .cursor/rules/changelog-and-version.mdc (always applied).

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=== Shield: changelog + version workflow ==="
echo ""
echo "After substantive code or config changes, the agent (or you) must:"
echo ""
echo "  1. Create changelogs/vX.Y.Z.md documenting summary, touched areas, and rationale."
echo "  2. Set version.properties → version=X.Y.Z (same as the new changelog)."
echo "  3. Do not delete or rewrite older changelogs/v*.md files."
echo ""
echo "Current version.properties:"
if [[ -f version.properties ]]; then
  grep -E '^version=' version.properties || true
else
  echo "  (missing version.properties)"
fi
echo ""
echo "Existing changelog files:"
if [[ -d changelogs ]]; then
  ls -1 changelogs/v*.md 2>/dev/null | sed 's/^/  /' || echo "  (none)"
else
  echo "  (missing changelogs/)"
fi
echo ""

VERIFY=false
if [[ "${1:-}" == "--verify" ]]; then
  VERIFY=true
fi

if $VERIFY; then
  ver=""
  if [[ -f version.properties ]]; then
    ver=$(grep -E '^version=' version.properties | head -1 | cut -d= -f2 | tr -d ' \r')
  fi
  if [[ -z "$ver" ]]; then
    echo "ERROR: could not read version= from version.properties" >&2
    exit 1
  fi
  f="changelogs/v${ver}.md"
  if [[ ! -f "$f" ]]; then
    echo "WARNING: no matching changelog for current version: $f" >&2
    echo "Create it after your next substantive change batch." >&2
    exit 1
  fi
  echo "OK: changelog exists for version $ver ($f)"
fi
