#!/bin/bash
# ContentFlow 服务器部署脚本
# 在服务器上以 root 运行: bash setup-server.sh
set -e

echo "=== ContentFlow 服务器部署 ==="

# 1. 系统依赖
echo ">>> 安装系统依赖..."
apt-get update
apt-get install -y python3.12 python3.12-venv postgresql postgresql-contrib nginx certbot python3-certbot-nginx git curl

# 如果 python3.12 不可用，用默认 python3
if ! command -v python3.12 &> /dev/null; then
    echo "python3.12 不可用，尝试安装..."
    apt-get install -y software-properties-common
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update
    apt-get install -y python3.12 python3.12-venv
fi

# 安装 uv
echo ">>> 安装 uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# 2. PostgreSQL 设置
echo ">>> 配置 PostgreSQL..."
sudo -u postgres psql -c "CREATE USER contentflow WITH PASSWORD 'contentflow_db_pass_2026';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE contentflow OWNER contentflow;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE contentflow TO contentflow;" 2>/dev/null || true

# 3. 创建应用用户和目录
echo ">>> 创建应用目录..."
useradd -m -s /bin/bash contentflow 2>/dev/null || true
mkdir -p /opt/contentflow
chown contentflow:contentflow /opt/contentflow

echo ""
echo "=== 系统依赖安装完成 ==="
echo ""
echo "接下来手动执行："
echo "1. 将代码上传到 /opt/contentflow/backend/"
echo "2. 运行 bash /opt/contentflow/deploy-app.sh"
