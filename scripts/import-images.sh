#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <path-to-image-archive.tar.gz>"
  exit 1
fi

ARCHIVE_PATH="$1"

if [ ! -f "${ARCHIVE_PATH}" ]; then
  echo "Archive not found: ${ARCHIVE_PATH}"
  exit 1
fi

echo "[1/2] Loading Docker images..."
gunzip -c "${ARCHIVE_PATH}" | docker load

echo "[2/2] Done"
echo "Loaded:"
echo "- xhs-publish-backend:latest"
echo "- xhs-publish-frontend:latest"
