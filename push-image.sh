#!/usr/bin/env bash
set -euo pipefail

GH_USER="hoangsonww"
IMAGE="ghcr.io/${GH_USER}/sql-mongo-converter"

# 1) extract version from setup.py (portable)
#    works on both macOS and Linux
VERSION=$(sed -nE "s/^[[:space:]]*version[[:space:]]*=[[:space:]]*['\"]([0-9]+\.[0-9]+\.[0-9]+)['\"].*/\1/p" setup.py)

if [ -z "${VERSION}" ]; then
  echo "❌ Could not parse version from setup.py"
  exit 1
fi

echo "ℹ️  Building and pushing version ${VERSION}"

# 2) require GITHUB_TOKEN
if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "❌ Please export GITHUB_TOKEN (with write:packages scope)."
  exit 1
fi

# 3) login to GitHub Container Registry
echo "${GITHUB_TOKEN}" | docker login ghcr.io -u "${GH_USER}" --password-stdin

# 4) build & tag
docker build \
  --pull \
  -t "${IMAGE}:${VERSION}" \
  -t "${IMAGE}:latest" \
  .

# 5) push
docker push "${IMAGE}:${VERSION}"
docker push "${IMAGE}:latest"

echo "✅ Pushed:"
echo "   • ${IMAGE}:${VERSION}"
echo "   • ${IMAGE}:latest"
