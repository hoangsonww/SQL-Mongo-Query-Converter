#!/usr/bin/env bash
# build.sh — clean + test + build your Python package

set -euo pipefail

# 1. Clean up old builds
echo "🧹 Cleaning up previous builds…"
rm -rf build/ dist/ *.egg-info/

# 2. Run your test suite (if you have one)
if command -v pytest &> /dev/null; then
  echo "🧪 Running tests…"
  pytest
else
  echo "⚠️  pytest not found — skipping tests"
fi

# 3. Ensure build tools are installed
echo "📦 Ensuring latest build tools…"
python3 -m pip install --upgrade build wheel twine

# 4. Build source & wheel
echo "🚧 Building source and wheel distributions…"
python3 -m build

# 5. Verify the distributions
echo "🔍 Checking distribution integrity…"
python3 -m twine check dist/*

echo "✅ Build complete — artifacts in dist/"
