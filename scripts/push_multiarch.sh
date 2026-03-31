#!/bin/sh
set -eu

IMAGE_REPO="${1:-${IMAGE_REPO:-}}"

if [ -z "${IMAGE_REPO}" ]; then
  echo "Usage: $0 <image-repo>"
  echo "Example: $0 ghcr.io/your-org/chrome-cdp-novnc"
  exit 1
fi

TAG="$(date -u +%Y%m%d-%H%M%S)"

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag "${IMAGE_REPO}:${TAG}" \
  --tag "${IMAGE_REPO}:latest" \
  --push \
  .

echo "Pushed:"
echo "  ${IMAGE_REPO}:${TAG}"
echo "  ${IMAGE_REPO}:latest"
