# 机加工报价辅助 — 后端

FastAPI 四层骨架（接口 / 用例 / 领域 / 适配器）。依赖用 `uv` 管理。

## 本地运行

```bash
# 在仓库根目录
docker compose up -d postgres   # 容器化 Postgres
cd backend
uv sync --group dev
QA_DATABASE_URL=postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant \
  uv run alembic upgrade head
QA_SEED_DEMO_DATA=true \
QA_DATABASE_URL=postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant \
QA_OBJECT_STORE_BACKEND=local \
QA_LOCAL_OBJECT_DIR=/tmp/quote-assistant-objects \
  uv run uvicorn quote_assistant.interface.http.app:app --reload --app-dir src
```

演示账号（种子数据）：

- 华东精密 **报价员**：`quoter_a` / `change-me-a`
- 南方模具 **报价员**：`quoter_b` / `change-me-b`

对象存储：用例层只依赖 `ObjectStorage` 窄接口（存 / 取 / 签发临时 URL / 删）。`QA_OBJECT_STORE_BACKEND=local` 时写入本地目录；`oss` 时走阿里云 OSS，put 时带 `x-oss-server-side-encryption: AES256` 与 private ACL，Bucket 本身不得公共读。

## 缝 1 测试

pytest + FastAPI ASGI 测试客户端（不起端口）。启动时对真实 Postgres 执行 Alembic。

有 Docker 时默认用 testcontainers 拉起 `postgres:16`；CI 则用 workflow 里的 Postgres service，并设置 `QA_TEST_DATABASE_URL`。

```bash
cd backend
uv run pytest
```
