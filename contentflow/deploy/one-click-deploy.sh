#!/bin/bash
# ContentFlow 一键部署脚本
# 用法: 在服务器上运行 bash one-click-deploy.sh
set -e

echo "========================================="
echo "  ContentFlow 一键部署"
echo "========================================="

# 1. 安装系统依赖
echo ""
echo "[1/7] 安装系统依赖..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv postgresql postgresql-contrib nginx git curl > /dev/null 2>&1
echo "  ✓ 系统依赖安装完成"

# 2. 安装 uv
echo "[2/7] 安装 uv..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1
fi
export PATH="$HOME/.local/bin:$PATH"
echo "  ✓ uv 已就绪"

# 3. 配置 PostgreSQL
echo "[3/7] 配置数据库..."
systemctl start postgresql
systemctl enable postgresql > /dev/null 2>&1
DB_PASS=$(openssl rand -hex 16)
sudo -u postgres psql -c "CREATE USER contentflow WITH PASSWORD '${DB_PASS}';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE contentflow OWNER contentflow;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER contentflow WITH PASSWORD '${DB_PASS}';" 2>/dev/null
echo "  ✓ 数据库已配置"

# 4. 下载代码
echo "[4/7] 下载代码..."
mkdir -p /opt/contentflow
if [ -d "/opt/contentflow/backend/.git" ]; then
    cd /opt/contentflow/backend && git pull
else
    # 从 GitHub clone（替换为你的仓库地址）
    REPO_URL="${REPO_URL:-https://github.com/kerro99920/contentflow.git}"
    BRANCH="${BRANCH:-feat/contentflow-phase1}"
    rm -rf /tmp/contentflow-clone
    git clone --depth 1 -b "$BRANCH" "$REPO_URL" /tmp/contentflow-clone 2>/dev/null
    cp -r /tmp/contentflow-clone/contentflow/backend /opt/contentflow/backend
    cp -r /tmp/contentflow-clone/contentflow/deploy /opt/contentflow/deploy
    rm -rf /tmp/contentflow-clone
fi
echo "  ✓ 代码已就绪"

# 5. 配置应用
echo "[5/7] 配置应用..."
JWT_SECRET=$(openssl rand -hex 32)
cd /opt/contentflow/backend

cat > .env << ENVEOF
DATABASE_URL=postgresql+asyncpg://contentflow:${DB_PASS}@localhost:5432/contentflow
TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db
REDIS_URL=
OMINILINK_API_KEY=sk-84fba3227d4a4bc1bc351ff80529b368
DASHSCOPE_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
JWT_SECRET=${JWT_SECRET}
FRONTEND_URL=
ENVEOF

uv sync --quiet
uv run python init_db.py 2>/dev/null || uv run alembic upgrade head
echo "  ✓ 应用已配置"

# 6. 创建 systemd 服务
echo "[6/7] 配置系统服务..."
cat > /etc/systemd/system/contentflow.service << 'SVCEOF'
[Unit]
Description=ContentFlow API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/contentflow/backend
Environment=PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/root/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

# Nginx 反向代理
cat > /etc/nginx/sites-available/contentflow << 'NGXEOF'
server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    location / {
        return 200 '{"message":"ContentFlow API Server","docs":"/api/health"}';
        add_header Content-Type application/json;
    }
}
NGXEOF

ln -sf /etc/nginx/sites-available/contentflow /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t > /dev/null 2>&1

systemctl daemon-reload
systemctl enable contentflow > /dev/null 2>&1
systemctl restart contentflow
systemctl restart nginx
echo "  ✓ 服务已启动"

# 7. 验证
echo "[7/7] 验证部署..."
sleep 3
if curl -s http://localhost:8000/api/health | grep -q "ok"; then
    echo ""
    echo "========================================="
    echo "  部署成功！"
    echo "========================================="
    echo ""
    echo "  API 地址: http://114.66.57.133/api/health"
    echo ""
    echo "  管理命令:"
    echo "    查看日志: journalctl -u contentflow -f"
    echo "    重启服务: systemctl restart contentflow"
    echo "    更新代码: cd /opt/contentflow/backend && git pull && systemctl restart contentflow"
    echo ""
else
    echo ""
    echo "  ✗ 启动失败！查看日志:"
    echo "    journalctl -u contentflow -n 30"
fi
