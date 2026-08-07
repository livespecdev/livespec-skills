#!/usr/bin/env bash
#
# update-spec.sh - re-vendor the LiveSpec format spec into reference/
#
# Pulls SPEC.md + CHEATSHEET.md from a *committed ref* of the upstream
# `livespec` repo (never its working tree), re-pins the format version
# across the plugin's docs, and reports what changed.
#
# Usage:
#   ./update-spec.sh [REF]
#     REF   tag / branch / commit in the livespec repo to vendor from.
#           Default: HEAD. Pass a tag (e.g. v1.0.0-draft.2) for a
#           reproducible, versioned pull.
#
# Env:
#   LIVESPEC_SRC   path to the upstream `livespec` checkout.
#                  Default: $HOME/Dev/livespec
#
# Why a ref and not `cp`: copying the working tree can vendor uncommitted,
# unreviewable edits. `git show <ref>:file` guarantees you ship exactly
# what is committed at a named, reproducible point.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REF="${1:-HEAD}"
SRC="${LIVESPEC_SRC:-$HOME/Dev/livespec}"
REF_DIR="$SCRIPT_DIR/reference"

# Files vendored verbatim from upstream (byte-identical copies).
FILES=(SPEC.md CHEATSHEET.md)

# Plugin docs that pin the format version in prose; kept in sync.
# Every skill and agent carries the pin in its "Format reference" note, so
# they are globbed in rather than listed one by one.
PINNED_DOCS=(
  "reference/README.md"
  "README.md"
  "CLAUDE.md"
)
for f in "$SCRIPT_DIR"/skills/*/SKILL.md "$SCRIPT_DIR"/agents/*.md; do
  if [ -f "$f" ]; then PINNED_DOCS+=("${f#"$SCRIPT_DIR"/}"); fi
done

die() { printf 'update-spec: %s\n' "$1" >&2; exit 1; }

# --- sanity checks ---------------------------------------------------------
[ -d "$SRC/.git" ] || die "upstream livespec repo not found at '$SRC' (set LIVESPEC_SRC)"
git -C "$SRC" rev-parse --verify --quiet "$REF^{commit}" >/dev/null \
  || die "ref '$REF' does not resolve in $SRC"

RESOLVED="$(git -C "$SRC" rev-parse --short "$REF")"
echo "Vendoring from $SRC @ $REF ($RESOLVED)"

# --- capture the currently pinned version (before we overwrite anything) ---
OLD_VER="$(grep -m1 -oE '`v[0-9][^`]*`' "$REF_DIR/README.md" 2>/dev/null | head -1 | tr -d '`' || true)"

# --- vendor the files from the committed ref -------------------------------
for f in "${FILES[@]}"; do
  git -C "$SRC" cat-file -e "$REF:$f" 2>/dev/null || die "missing '$f' at $REF in $SRC"
  git -C "$SRC" show "$REF:$f" > "$REF_DIR/$f"
  echo "  vendored reference/$f"
done

# --- extract the new version from the freshly vendored SPEC.md -------------
NEW_VER="$(grep -m1 -E '^\*\*Version:\*\*' "$REF_DIR/SPEC.md" \
            | grep -oE '`[^`]+`' | head -1 | tr -d '`' || true)"
[ -n "$NEW_VER" ] || die "could not read **Version:** from vendored SPEC.md"

# --- re-pin the version across the plugin docs -----------------------------
if [ -n "$OLD_VER" ] && [ "$OLD_VER" != "$NEW_VER" ]; then
  echo "Version: $OLD_VER -> $NEW_VER (re-pinning docs)"
  OLD_ESC="${OLD_VER//./\\.}"
  for d in "${PINNED_DOCS[@]}"; do
    path="$SCRIPT_DIR/$d"
    [ -f "$path" ] || continue
    if grep -q "$OLD_VER" "$path"; then
      # portable in-place edit (works with both BSD and GNU sed)
      tmp="$(mktemp)"
      sed "s|${OLD_ESC}|${NEW_VER}|g" "$path" > "$tmp" && mv "$tmp" "$path"
      echo "  re-pinned $d"
    fi
  done
else
  echo "Version unchanged ($NEW_VER); files refreshed"
fi

# --- report ----------------------------------------------------------------
echo
echo "Done. Review the diff before committing:"
echo "  git -C \"$SCRIPT_DIR\" diff --stat"
