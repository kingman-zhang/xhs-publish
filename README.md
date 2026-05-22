# 小红书文案管理与扫码发布 MVP

一个面向小红书运营场景的后台管理系统，支持：

- 图文文案的新建、编辑、删除、搜索
- 图片上传、封面设置、顺序调整
- 二维码分享与手机扫码预览
- 通过小红书 JS SDK 触发发布

## 技术栈

- 前端：React + Vite + TypeScript
- 后端：FastAPI + Pydantic
- 数据库：MongoDB
- 部署：Docker Compose（前端容器直接对外暴露端口）

## 目录结构

```text
xhs_publish/
├── backend/
├── frontend/
├── nginx/
├── docker-compose.yml
└── .env.example
```

## 本地开发

1. 复制环境变量：

```bash
cp .env.example .env.dev
```

2. 启动后端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

3. 启动前端：

```bash
cd frontend
npm install
npm run dev
```

前端开发默认会把 `/api` 代理到 `http://localhost:8000`。

## Docker 部署

```bash
cp .env.example .env.dev
docker compose --env-file .env.dev up --build -d
```

## 本地构建镜像并复制到服务器

如果你不想在服务器上执行前端构建，可以在本地先把镜像打好，再导出后上传：

```bash
cd /Users/zhangjianwen/Documents/Kingman/code/codex/xhs_publish
bash scripts/export-images.sh
```

脚本会生成类似这样的文件：

```text
artifacts/xhs-publish-images-20260521-160000.tar.gz
```

然后把这个压缩包传到服务器，例如：

```bash
scp artifacts/xhs-publish-images-*.tar.gz user@your-server:/opt/xhs-publish/
```

在服务器上加载镜像：

```bash
cd /opt/xhs-publish
bash scripts/import-images.sh ./xhs-publish-images-20260521-160000.tar.gz
```

镜像加载后，服务器上只需要准备：

- 项目目录里的 `docker-compose.yml`
- 对应的 `.env.prod`
- `scripts/import-images.sh`

然后直接启动：

```bash
docker compose --env-file .env.prod up -d
```

如果你改了代码，需要重新导出并重新上传新的镜像包。

## 本地构建前端产物，服务器再构建镜像

如果你希望前端代码在本地完成构建，而服务器只负责 Docker 构建和启动，可以使用发布包模式：

```bash
cd /Users/zhangjianwen/Documents/Kingman/code/codex/xhs_publish
bash scripts/package-release.sh
```

它会：

- 在本地执行前端 `npm run build`
- 打包后端源码
- 打包前端 `dist`
- 生成一个可上传到服务器的发布包

发布包会在：

```text
artifacts/xhs-publish-release-YYYYMMDD-HHMMSS.tar.gz
```

上传到服务器后解压：

```bash
mkdir -p /opt/xhs-publish
tar -xzf xhs-publish-release-YYYYMMDD-HHMMSS.tar.gz -C /opt/xhs-publish
```

服务器上的 `.env.prod` 里需要设置：

```env
FRONTEND_DOCKERFILE=Dockerfile.release
```

然后在服务器上启动：

```bash
cd /opt/xhs-publish
docker compose --env-file .env.prod up -d --build
```

## 一键部署脚本

如果你希望本地一键完成：

- 构建前端 `dist`
- 生成发布包
- 上传到服务器
- 服务器解压
- 服务器构建镜像并启动

可以直接使用：

```bash
cd /Users/zhangjianwen/Documents/Kingman/code/codex/xhs_publish
bash scripts/ci.sh
```

默认配置写在脚本顶部，也支持用环境变量覆盖，例如：

```bash
SERVER_USER=ubuntu \
SERVER_IP=1.2.3.4 \
SERVER_APP_DIR=/opt/xhs-publish \
SERVER_ENV_FILE=.env.prod \
SERVER_NETWORK_NAME=default_net \
bash scripts/ci.sh
```

脚本会在服务器上保留多份发布版本，并自动把 `current` 软链接切到最新版本。

## 环境文件建议

推荐按环境分别维护：

- `.env.dev`
- `.env.prod`
- `.env.example`

启动时显式指定：

```bash
docker compose --env-file .env.dev up -d --build
docker compose --env-file .env.prod up -d
```

注意：

- `service.env_file` 不参与 Compose 的 `${VAR}` 插值，容易和根目录默认 `.env` 混淆，所以当前项目不再使用它。
- 如果 MongoDB 跑在宿主机上，容器里不要写 `localhost`，请写：

```env
MONGO_URL=mongodb://root:密码@host.docker.internal:27017/xhs?authSource=admin
```

- 如果 MongoDB 跑在 Docker 网络中的另一个容器上，则写容器服务名，例如：

```env
MONGO_URL=mongodb://root:密码@mongo:27017/xhs?authSource=admin
```

## 关键环境变量

- `MONGO_URL`：MongoDB 连接串
- `MONGO_DB_NAME`：数据库名
- `PUBLIC_BASE_URL`：公网访问域名，用于生成分享链接与二维码
- `UPLOAD_DIR`：容器内图片目录，通常保持 `/data/xhs-publish/uploads`
- `UPLOAD_HOST_DIR`：宿主机挂载目录；本地 macOS 建议用 `./uploads`，服务器可用真实磁盘路径
- `FRONTEND_PORT`：前端容器对外暴露端口，默认 `5174`
- `XHS_APP_KEY`：小红书开放平台 appKey
- `XHS_APP_SECRET`：小红书开放平台 appSecret
- `XHS_ACCESS_TOKEN_URL`：小红书 access_token 接口，默认已内置
- `XHS_REQUEST_TIMEOUT_MS`：请求小红书接口的超时时间

## 小红书签名说明

分享页的“发布到小红书”按钮会优先调用小红书 JS SDK。  
要让签名真正生效，只需要在服务端配置可用的 `XHS_APP_KEY` 和 `XHS_APP_SECRET`。后端会自动向小红书拉取 `access_token` 并在内存中缓存；如果未配置密钥，系统会自动降级为仅展示预览与兼容性提示。
