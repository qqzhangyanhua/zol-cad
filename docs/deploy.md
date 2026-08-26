# 部署说明（票 27）

## 决定：单进程

MVP 的负载是一家工厂、几个报价员。部署形态钉死为：

- **一个** uvicorn 进程（`--workers 1`）
- **一个** 应用副本（不要水平扩出第二个实例）
- **不要** 用 `--reload` 跑生产

启动时的滞留回收会把「已上传 / 分级中 / 提取中」改成**提取失败**。这个 sweep 只在「重启后没有别人还在跑这些作业」时正确——也就是单进程。

`uvicorn --workers N`、滚动双实例、或任何第二个副本，都会把另一个进程正在处理的**零件图**改成失败，随后两个进程互相覆盖状态。

以后若要多进程 / 零停机滚动发布，必须先做锁或租约，只回收真正无主的作业。那不在本票范围。

生产入口：`backend/scripts/run-production.sh` 和 `backend/Dockerfile`。二者都禁止 `--reload`，并把 workers 钉在 1。

同一进程内的后台线程与「重试」仍可能并发。行级 `FOR UPDATE` 会挡住双跑，并把事件 `sequence_no` 串起来。

## 必须覆盖的配置

非本地环境（`QA_APP_ENV` 不是 `local` / `dev` / `development` / `test`）启动时会校验。下列占位值必须被覆盖，否则**拒绝启动**：

| 变量 | 禁止的默认值 |
| --- | --- |
| `QA_OBJECT_SIGN_SECRET` | `dev-object-sign-secret` |
| `QA_DEMO_PASSWORD_A` | `change-me-a` |
| `QA_DEMO_PASSWORD_B` | `change-me-b` |

Session cookie 在非本地默认带 `Secure`。本地 HTTP 开发可设 `QA_SESSION_COOKIE_SECURE=false`。

## 建议的生产环境变量

```bash
QA_APP_ENV=production
QA_DATABASE_URL=postgresql+psycopg://...
QA_OBJECT_SIGN_SECRET=<随机长密钥>
QA_DEMO_PASSWORD_A=<覆盖种子密码>
QA_DEMO_PASSWORD_B=<覆盖种子密码>
QA_SESSION_COOKIE_SECURE=true
QA_OBJECT_STORE_BACKEND=oss   # 或继续 local，仅限受控环境
QA_EXTRACTION_ENGINE=fixture  # 票 02 关闭前不得当已选定供应商
QA_PART_DRAWING_PROCESSOR=thread
QA_PART_DRAWING_PROCESSOR_WORKERS=4
QA_PART_DRAWING_PROCESSOR_QUEUE_MAX=64
QA_EXTRACTION_TIMEOUT_SECONDS=60
QA_EXTRACTION_RETRY_COUNT=1
QA_LOG_LEVEL=INFO
```

## 健康检查

`GET /health` 会对数据库执行 `SELECT 1`。连不上库返回 503，负载均衡器应把该实例摘掉。

## 容器

```bash
cd backend
docker build -t quote-assistant-api .
docker run --rm -p 8000:8000 --env-file .env.production quote-assistant-api
```

镜像入口会先跑 Alembic，再以 **1 个 worker** 启动 uvicorn。
