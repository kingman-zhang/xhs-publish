#!/usr/bin/env bash
set -euo pipefail

# =========================
# 基础配置
# =========================

APP_NAME="${APP_NAME:-xhs-publish}"
SERVER_USER="${SERVER_USER:-ubuntu}"
SERVER_IP="${SERVER_IP:-119.29.14.238}"
SERVER_APP_DIR="${SERVER_APP_DIR:-/data/xhs-publish}"
SERVER_ENV_FILE="${SERVER_ENV_FILE:-.env.prod}"
SERVER_NETWORK_NAME="${SERVER_NETWORK_NAME:-software_app-net}"
KEEP_RELEASES="${KEEP_RELEASES:-5}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ARTIFACT_DIR="${ROOT_DIR}/artifacts"
VERSION="$(date +"%Y%m%d%H%M%S")"
PACKAGE_NAME="${APP_NAME}-release-${VERSION}.tar.gz"
LOCAL_PACKAGE_PATH="${ARTIFACT_DIR}/${PACKAGE_NAME}"
REMOTE_RELEASE_DIR="${SERVER_APP_DIR}/releases"
REMOTE_PACKAGE_PATH="${REMOTE_RELEASE_DIR}/${PACKAGE_NAME}"
REMOTE_CURRENT_DIR="${SERVER_APP_DIR}/current"

echo "=============================="
echo "开始部署：${APP_NAME}"
echo "版本号：${VERSION}"
echo "服务器：${SERVER_USER}@${SERVER_IP}"
echo "=============================="

# =========================
# 1. 本地构建发布包
# =========================

echo "1. 本地构建发布包..."
cd "${ROOT_DIR}"
bash "${SCRIPT_DIR}/package-release.sh"

LATEST_PACKAGE="$(ls -t "${ARTIFACT_DIR}"/xhs-publish-release-*.tar.gz | head -n 1)"

if [ -z "${LATEST_PACKAGE}" ] || [ ! -f "${LATEST_PACKAGE}" ]; then
  echo "未找到发布包，部署失败"
  exit 1
fi

cp "${LATEST_PACKAGE}" "${LOCAL_PACKAGE_PATH}"
echo "发布包准备完成：${LOCAL_PACKAGE_PATH}"

# =========================
# 2. 上传发布包到服务器
# =========================

echo "2. 上传发布包到服务器..."
ssh "${SERVER_USER}@${SERVER_IP}" "mkdir -p '${REMOTE_RELEASE_DIR}'"
scp "${LOCAL_PACKAGE_PATH}" "${SERVER_USER}@${SERVER_IP}:${REMOTE_PACKAGE_PATH}"
echo "上传完成"

# =========================
# 3. 服务器解压、切换、构建、启动
# =========================

echo "3. 远程部署并启动..."

ssh "${SERVER_USER}@${SERVER_IP}" << EOF
set -euo pipefail

APP_NAME="${APP_NAME}"
SERVER_APP_DIR="${SERVER_APP_DIR}"
REMOTE_RELEASE_DIR="${REMOTE_RELEASE_DIR}"
REMOTE_CURRENT_DIR="${REMOTE_CURRENT_DIR}"
REMOTE_PACKAGE_PATH="${REMOTE_PACKAGE_PATH}"
SERVER_ENV_FILE="${SERVER_ENV_FILE}"
SERVER_NETWORK_NAME="${SERVER_NETWORK_NAME}"
KEEP_RELEASES="${KEEP_RELEASES}"
VERSION="${VERSION}"

RELEASE_DIR="\${REMOTE_RELEASE_DIR}/release-\${VERSION}"

mkdir -p "\${RELEASE_DIR}"
tar -xzf "\${REMOTE_PACKAGE_PATH}" -C "\${RELEASE_DIR}"

if ! docker network inspect "\${SERVER_NETWORK_NAME}" >/dev/null 2>&1; then
  echo "Docker 网络 \${SERVER_NETWORK_NAME} 不存在，正在创建..."
  docker network create "\${SERVER_NETWORK_NAME}"
fi

if [ ! -f "\${SERVER_APP_DIR}/\${SERVER_ENV_FILE}" ]; then
  echo "缺少环境文件：\${SERVER_APP_DIR}/\${SERVER_ENV_FILE}"
  exit 1
fi

ln -sfn "\${RELEASE_DIR}" "\${REMOTE_CURRENT_DIR}"
cp "\${SERVER_APP_DIR}/\${SERVER_ENV_FILE}" "\${REMOTE_CURRENT_DIR}/\${SERVER_ENV_FILE}"

cd "\${REMOTE_CURRENT_DIR}"

echo "使用环境文件启动：\${SERVER_ENV_FILE}"
docker compose --env-file "\${SERVER_ENV_FILE}" up -d --build

echo "清理旧发布目录，只保留最近 \${KEEP_RELEASES} 个..."
ls -dt "\${REMOTE_RELEASE_DIR}"/release-* 2>/dev/null | tail -n +\$((KEEP_RELEASES + 1)) | xargs -r rm -rf

echo "清理已上传的压缩包，只保留最近 \${KEEP_RELEASES} 个..."
ls -t "\${REMOTE_RELEASE_DIR}"/*.tar.gz 2>/dev/null | tail -n +\$((KEEP_RELEASES + 1)) | xargs -r rm -f

echo "容器状态："
docker ps --filter "name=xhs-publish"
EOF

echo "=============================="
echo "部署完成"
echo "版本：${PACKAGE_NAME}"
echo "=============================="
