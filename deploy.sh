#!/bin/bash
set -e

#SERVER_IP=${1:-""}
#if [ -z "$SERVER_IP" ]; then
#  echo "用法: ./deploy.sh <服务器IP>"
#  echo "示例: ./deploy.sh 192.168.1.100"
#  exit 1
#fi

SSH_USER=${SSH_USER:-root}
SSH_PORT=${SSH_PORT:-22}
DST_DIR="/z/docker/jay_words"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== 部署 jay-words 到 $SERVER_IP ==="

# 1. 本地备份旧版本（映射目录即服务器目录）
if [ -d "$DST_DIR" ]; then
  echo "备份旧版本到 ${DST_DIR}_backup_$TIMESTAMP ..."
  mv "$DST_DIR" "${DST_DIR}_backup_$TIMESTAMP"
fi

# 2. 拷贝代码到映射目录
echo "拷贝代码到 $DST_DIR ..."
mkdir -p /z/docker
cp -r "$SRC_DIR" "$DST_DIR"
# 清理不需要的文件
rm -rf "$DST_DIR/.git" "$DST_DIR/frontend/node_modules" "$DST_DIR/backend/__pycache__" 2>/dev/null || true
find "$DST_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$DST_DIR" -name "*.pyc" -delete 2>/dev/null || true

## 3. 远程检查 .env 并部署
#echo "连接服务器并部署..."s
#ssh -p $SSH_PORT ${SSH_USER}@${SERVER_IP} "
#  cd $DST_DIR
#
#  if [ ! -f .env ]; then
#    echo 'DB_HOST=127.0.0.1
#DB_PORT=3306
#DB_USER=jay
#DB_PASSWORD=your_password_here
#DB_NAME=jay_words' > .env
#    echo '请先在服务器上编辑 $DST_DIR/.env 填写数据库密码'
#    echo '然后执行: cd $DST_DIR && docker compose up -d --build'
#    exit 1
#  fi
#
#  docker compose down --remove-orphans 2>/dev/null || true
#  docker compose up -d --build
#"
#
#echo "=== 部署完成 ==="
#echo "访问 http://$SERVER_IP:18001"
