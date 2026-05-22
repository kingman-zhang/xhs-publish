#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACT_DIR="${ROOT_DIR}/artifacts"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE_PATH="${ARTIFACT_DIR}/xhs-publish-images-${TIMESTAMP}.tar.gz"

mkdir -p "${ARTIFACT_DIR}"

cd "${ROOT_DIR}"

echo "[1/3] Building Docker images..."
docker compose build

echo "[2/3] Exporting images..."
docker save xhs-publish-backend:latest xhs-publish-frontend:latest | gzip > "${ARCHIVE_PATH}"

echo "[3/3] Done"
echo "Archive created at:"
echo "${ARCHIVE_PATH}"
