# 机加工报价辅助

面向服务型机加工厂的报价辅助工具。本仓库当前落地到票 11：**管理员**可录入纯人工基线，并对照本厂已复核零件图的处理耗时（上传 → 已复核），用客观数据判断是否省时。未复核零件图不计入统计。票 10 的不可变**修正记录**与全厂修改频次统计仍在。

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
| 华东精密 | 管理员 | `admin_a` | `change-me-a` |
| 南方模具 | 报价员 | `quoter_b` | `change-me-b` |
| 南方模具 | 管理员 | `admin_b` | `change-me-b` |
