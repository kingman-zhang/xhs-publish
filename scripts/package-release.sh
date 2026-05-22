#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ARTIFACT_DIR="${ROOT_DIR}/artifacts"
STAGING_DIR="${ARTIFACT_DIR}/release-package"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE_PATH="${ARTIFACT_DIR}/xhs-publish-release-${TIMESTAMP}.tar.gz"

mkdir -p "${ARTIFACT_DIR}"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

echo "[1/5] Building frontend dist..."
(
  cd "${ROOT_DIR}/frontend"
  npm run build
)

echo "[2/5] Preparing release directory..."
mkdir -p "${STAGING_DIR}/backend" "${STAGING_DIR}/frontend" "${STAGING_DIR}/scripts"

cp "${ROOT_DIR}/docker-compose.yml" "${STAGING_DIR}/"
cp "${ROOT_DIR}/README.md" "${STAGING_DIR}/"
cp "${ROOT_DIR}/.env.example" "${STAGING_DIR}/"

cp "${ROOT_DIR}/backend/Dockerfile" "${STAGING_DIR}/backend/"
cp "${ROOT_DIR}/backend/requirements.txt" "${STAGING_DIR}/backend/"
cp -R "${ROOT_DIR}/backend/app" "${STAGING_DIR}/backend/"

cp "${ROOT_DIR}/frontend/Dockerfile.release" "${STAGING_DIR}/frontend/"
cp "${ROOT_DIR}/frontend/nginx.conf.template" "${STAGING_DIR}/frontend/"
cp -R "${ROOT_DIR}/frontend/dist" "${STAGING_DIR}/frontend/"

cp "${ROOT_DIR}/scripts/import-images.sh" "${STAGING_DIR}/scripts/"

echo "[3/5] Writing release compose override hint..."
cat > "${STAGING_DIR}/DEPLOY.md" <<'EOF'
Use the prebuilt frontend dist on the server by setting:

FRONTEND_DOCKERFILE=Dockerfile.release

Then start with:

docker compose --env-file .env.prod up -d --build
EOF

echo "[4/5] Creating archive..."
tar -czf "${ARCHIVE_PATH}" -C "${STAGING_DIR}" .

echo "[5/5] Done"
echo "Release package created at:"
echo "${ARCHIVE_PATH}"
