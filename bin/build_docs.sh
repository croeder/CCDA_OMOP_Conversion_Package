#!/usr/bin/env zsh
# Regenerate API docs and rebuild HTML.
# Run after major code changes (new modules, significant docstring updates).
#
# Requires: pip install sphinx sphinx-rtd-theme
#
# Usage: bin/build_docs.sh [--open]

set -e

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC="$REPO_ROOT/src/ccda_to_omop"
DOCS="$REPO_ROOT/docs"

cd "$REPO_ROOT"

echo "==> Generating metadata config docs..."
python3 "$DOCS/gen_metadata_docs.py"

echo "==> Regenerating API stubs from source..."
sphinx-apidoc \
    --force \
    --module-first \
    --separate \
    -o "$DOCS/api" \
    "$SRC" \
    "$SRC/metadata"   # exclude: hyphenated filenames break autodoc

echo "==> Building HTML..."
sphinx-build -b html "$DOCS" "$DOCS/_build/html"

echo ""
echo "Done. Docs at: $DOCS/_build/html/index.html"

if [[ "$1" == "--open" ]]; then
    open "$DOCS/_build/html/index.html"
fi
