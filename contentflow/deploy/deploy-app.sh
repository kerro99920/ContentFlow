#!/bin/bash
# ContentFlow 应用部署脚本
# 在服务器上以 root 运行: bash deploy-app.sh
set -e

APP_DIR="/opt/contentflow/backend"
export PATH="$HOME/.local/bin:$PATH"

echo "=== 部署 ContentFlow 后端 ==="

# 1. 创建 .env
if [ ! -f "$APP_DIR/.env" ]; then
    echo ">>> 创建 .env 配置..."
    JWT_SECRET=$(openssl rand -hex 32)
    cat > "$APP_DIR/.env" << EOF
DATABASE_URL=postgresql+asyncpg://contentflow:contentflow_db_pass_2026@localhost:5432/contentflow
TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=${JWT_SECRET}
ANTHROPIC_API_KEY=填入你的key
OPENAI_API_KEY=
FRONTEND_URL=https://你的vercel域名
EOF
    echo "!!! 请编辑 $APP_DIR/.env 填入 ANTHROPIC_API_KEY 和 FRONTEND_URL !!!"
fi

# 2. 安装依赖
echo ">>> 安装 Python 依赖..."
cd "$APP_DIR"
uv sync

# 3. 运行数据库迁移
echo ">>> 运行数据库迁移..."
uv run alembic upgrade head

# 4. 创建 systemd 服务
echo ">>> 配置 systemd 服务..."
cat > /etc/systemd/system/contentflow.service << EOF
[Unit]
Description=ContentFlow API
After=network.target postgresql.service

[Service]
Type=simple
User=contentflow
WorkingDirectory=/opt/contentflow/backend
ExecStart=/root/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
Environment=PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

# 5. 配置 Nginx 反向代理
echo ">>> 配置 Nginx..."
cat > /etc/nginx/sites-available/contentflow << 'EOF'
server {
    listen 80;
    server_name 114.66.57.133;

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/contentflow /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

# 6. 启动服务
echo ">>> 启动服务..."
systemctl daemon-reload
systemctl enable contentflow
systemctl restart contentflow
systemctl restart nginx

# 7. 验证
echo ">>> 等待服务启动..."
sleep 3
if curl -s http://localhost:8000/api/health | grep -q "ok"; then
    echo ""
    echo "=== 部署成功！ ==="
    echo "API 地址: http://114.66.57.133/api/health"
    echo ""
    echo "下一步："
    echo "1. 编辑 /opt/contentflow/backend/.env 填入 ANTHROPIC_API_KEY"
    echo "2. systemctl restart contentflow"
    echo "3. Vercel 前端设置 NEXT_PUBLIC_API_URL=http://114.66.57.133"
else
    echo "!!! 启动失败，检查日志: journalctl -u contentflow -n 50"
fi
