# 机加工报价辅助

面向服务型机加工厂的报价辅助工具。本仓库当前落地到票 14：**报价员**可在**报价任务**上导出一份每个零件一行的**报价底稿**（xlsx / csv）。列与顺序读该工厂后台模板（onboarding 配好，不进管理员界面）。未完成复核的零件图会拦住导出并点名。

## 结构

- `backend/` — FastAPI，四层（接口 / 用例 / 领域 / 适配器），Postgres + Alembic，缝 1 测试
- `frontend/` — Next.js，BFF 代理到后端
- `compose.yaml` — 容器化 Postgres
- `docs/deploy.md` — 生产部署（**单进程**，不要 `--workers N` / 不要第二副本）

生产入口见 `backend/Dockerfile` 与 `backend/scripts/run-production.sh`。启动回收假定重启后没有其他进程还在跑分级 / 读图取数；多进程会互相踩滞留作业。

## 快速启动

```bash
./dev.sh
```

会启动 Postgres、跑迁移、再同时拉起后端和前端。浏览器打开 http://127.0.0.1:3000 。`Ctrl+C` 停止前后端（Postgres 容器保持运行）。

手动分步启动：

```bash
docker compose up -d postgres

cd backend
uv sync --group dev
QA_DATABASE_URL=postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant \
  uv run alembic upgrade head
QA_APP_ENV=local \
QA_SESSION_COOKIE_SECURE=false \
QA_SEED_DEMO_DATA=true \
QA_OBJECT_STORE_BACKEND=local \
QA_LOCAL_OBJECT_DIR=/tmp/quote-assistant-objects \
  uv run uvicorn quote_assistant.interface.http.app:app --reload --app-dir src
```

另开一个终端：

```bash
cd frontend
pnpm install
pnpm dev
```

演示账号：

| 工厂 | 角色 | 账号 | 密码 |
| --- | --- | --- | --- |
| 华东精密 | 报价员 | `quoter_a` | `change-me-a` |
| 华东精密 | 管理员 | `admin_a` | `change-me-a` |
| 南方模具 | 报价员 | `quoter_b` | `change-me-b` |
| 南方模具 | 管理员 | `admin_b` | `change-me-b` |
