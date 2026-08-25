# 机加工报价辅助

面向服务型机加工厂的报价辅助工具。本仓库当前落地到票 08：**报价员**在并排界面上确认或就地修改提取值，处理完所有需确认项后把零件图标记为已复核。尺寸与公差无论图纸质量分级如何一律需确认；该判定表只活在后端领域层。

## 结构

- `backend/` — FastAPI，四层（接口 / 用例 / 领域 / 适配器），Postgres + Alembic，缝 1 测试
- `frontend/` — Next.js，BFF 代理到后端
- `compose.yaml` — 容器化 Postgres

## 快速启动

```bash
docker compose up -d postgres

cd backend
uv sync --group dev
QA_DATABASE_URL=postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant \
  uv run alembic upgrade head
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
| 南方模具 | 报价员 | `quoter_b` | `change-me-b` |
