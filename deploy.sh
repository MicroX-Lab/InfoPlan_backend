#!/bin/bash
# InfoPlan Backend - 阿里云一键部署/更新脚本
# 用法: ./deploy.sh [--rebuild]
#   默认: git pull + 重建镜像 + 重启容器
#   --rebuild: 强制无缓存重建镜像

set -e

APP_NAME="infoplan"
APP_DIR="/opt/InfoPlan_backend"
IMAGE_NAME="infoplan-backend"
PORT=5001
REPO_URL="https://github.com/MicroX-Lab/InfoPlan_backend.git"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# 1. 拉取最新代码
if [ -d "$APP_DIR/.git" ]; then
    log "拉取最新代码..."
    cd "$APP_DIR"
    git fetch origin main
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)
    if [ "$LOCAL" = "$REMOTE" ]; then
        warn "代码已是最新 ($LOCAL)"
    else
        git pull origin main
        log "代码已更新: $(git log --oneline -1)"
    fi
else
    log "首次部署，克隆仓库..."
    rm -rf "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# 2. 确保 .env 存在
if [ ! -f "$APP_DIR/.env" ]; then
    if [ -f "$APP_DIR/.env.example" ]; then
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        warn ".env 不存在，已从 .env.example 复制，请手动编辑配置!"
    else
        error ".env 和 .env.example 均不存在，请先创建 .env 文件"
    fi
fi

# 3. 构建 Docker 镜像
BUILD_ARGS=""
if [ "$1" = "--rebuild" ]; then
    BUILD_ARGS="--no-cache"
    log "强制无缓存重建镜像..."
else
    log "构建 Docker 镜像 (使用缓存)..."
fi
docker build $BUILD_ARGS -t "$IMAGE_NAME" "$APP_DIR"

# 4. 停止并删除旧容器
if docker ps -a --format '{{.Names}}' | grep -q "^${APP_NAME}$"; then
    log "停止旧容器..."
    docker stop "$APP_NAME" 2>/dev/null || true
    docker rm "$APP_NAME" 2>/dev/null || true
fi

# 5. 启动新容器
log "启动新容器..."
docker run -d \
    --name "$APP_NAME" \
    --restart unless-stopped \
    --env-file "$APP_DIR/.env" \
    -p ${PORT}:${PORT} \
    -v "${APP_DIR}/instance:/app/instance" \
    "$IMAGE_NAME"

# 6. 等待服务启动并验证
log "等待服务启动..."
sleep 3

if docker ps --format '{{.Names}}' | grep -q "^${APP_NAME}$"; then
    # 健康检查
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:${PORT}/api/auth/register" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" != "000" ]; then
        log "服务启动成功! HTTP 状态: ${HTTP_CODE}"
    else
        warn "容器已运行，但 HTTP 检查未通过，可能仍在启动中"
    fi
    log "容器状态:"
    docker ps --filter "name=${APP_NAME}" --format "  ID: {{.ID}}\n  状态: {{.Status}}\n  端口: {{.Ports}}"
else
    error "容器启动失败! 查看日志: docker logs ${APP_NAME}"
fi

# 7. 清理悬空镜像
DANGLING=$(docker images -f "dangling=true" -q)
if [ -n "$DANGLING" ]; then
    log "清理旧镜像..."
    docker rmi $DANGLING 2>/dev/null || true
fi

log "部署完成! 服务地址: http://$(hostname -I | awk '{print $1}'):${PORT}"
