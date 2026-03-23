#!/bin/bash
# ContentFlow 更新脚本 - 拉取最新代码并重启
set -e
export PATH="$HOME/.local/bin:$PATH"

cd /opt/contentflow/backend
git pull
uv sync
uv run alembic upgrade head
systemctl restart contentflow
echo "更新完成！"
