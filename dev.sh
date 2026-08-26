#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "缺少 $1，请先安装后再运行。" >&2
    exit 1
  fi
}

need docker
need uv
need pnpm

export QA_DATABASE_URL="${QA_DATABASE_URL:-postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant}"
export QA_APP_ENV="${QA_APP_ENV:-local}"
export QA_SESSION_COOKIE_SECURE="${QA_SESSION_COOKIE_SECURE:-false}"
export QA_SEED_DEMO_DATA="${QA_SEED_DEMO_DATA:-true}"
export QA_OBJECT_STORE_BACKEND="${QA_OBJECT_STORE_BACKEND:-local}"
export QA_LOCAL_OBJECT_DIR="${QA_LOCAL_OBJECT_DIR:-/tmp/quote-assistant-objects}"

echo "启动 Postgres..."
docker compose up -d postgres
echo "等待 Postgres 就绪..."
ready=0
for _ in $(seq 1 40); do
  if docker compose exec -T postgres pg_isready -U quote -d quote_assistant >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.5
done
if [[ "$ready" -ne 1 ]]; then
  echo "Postgres 未就绪，请检查 docker compose 日志。" >&2
  exit 1
fi

echo "准备后端..."
(
  cd backend
  uv sync --group dev
  uv run alembic upgrade head
)

echo "准备前端..."
(
  cd frontend
  pnpm install
)

cleanup() {
  trap - EXIT INT TERM
  echo
  echo "正在停止前后端（Postgres 容器保持运行）..."
  kill 0 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "启动后端 http://127.0.0.1:8000"
(
  cd backend
  exec uv run uvicorn quote_assistant.interface.http.app:app --reload --app-dir src --host 127.0.0.1 --port 8000
) &

echo "启动前端 http://127.0.0.1:3000"
(
  cd frontend
  exec pnpm dev
) &

echo
echo "已启动：http://127.0.0.1:3000"
echo "演示账号：quoter_a / change-me-a （管理员 admin_a / change-me-a）"
echo "Ctrl+C 停止前后端"
echo

wait
