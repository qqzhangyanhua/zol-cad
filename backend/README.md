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

- 华东精密 **报价员**：`quoter_a` / `change-me-a`；**管理员**：`admin_a` / `change-me-a`
- 南方模具 **报价员**：`quoter_b` / `change-me-b`；**管理员**：`admin_b` / `change-me-b`

对象存储：用例层只依赖 `ObjectStorage` 窄接口（存 / 取 / 签发临时 URL / 删）。`QA_OBJECT_STORE_BACKEND=local` 时写入本地目录；`oss` 时走阿里云 OSS，put 时带 `x-oss-server-side-encryption: AES256` 与 private ACL，Bucket 本身不得公共读。

提取引擎：用例层只依赖 `ExtractionEngine` Port（输入图像/PDF 页 + 零件族标识 + 输入图标识，输出结构化提取与图纸质量分级）。`QA_EXTRACTION_ENGINE` 默认 `fixture`（假实现，缝 1 用）；`vendor` 打开未选定供应商的骨架适配器，**不会调用付费 API**。票 02 / ADR-0009 关闭前不得把骨架当成已选定供应商。引擎原始输出在适配器边界用 Pydantic 严格校验，校验失败按提取失败处理，脏数据不进领域层。调用日志只记 `input_drawing_id` / 介质 / 字节数，不落图像内容。单张调用走 `ExtractionCostRecorder` 计数钩子，供应商未定时费用字段为 `None`。

风险标签：领域层纯函数 `evaluate_risk_labels`，输入当前结构化字段，输出标签列表（规则标识 / 触发值 / 理由）。词表不含「安全 / 无风险 / 通过」。门槛为 ADR-0007 示例与接线占位，待票 01 调研替换。标签现算不落库。

复核：领域层静态表 `FIELD_RISK_CLASS_BY_KEY` 判定高风险字段（尺寸类 / 公差类）一律需确认，分级只影响低风险字段。前端只展示后端给出的 `requires_confirmation`，不参与判断。存在未处理需确认项时，标记已复核被拒绝。报价员可忽略不适用项（忽略项不阻塞已复核、仍可见可撤销）、补录 AI 漏提的关键尺寸（与提取项同等对待，进入风险标签计算），以及在已复核后重新打开修改。修正后风险标签按确认值重算；重试提取保留已有复核修改。

修正记录：每次修改提取值或手工补录追加一条不可变记录（原值 → 新值、字段标识、字段类型、操作人、时间、所属零件图）。补录的原值为空。同一字段多次修改产生多条记录，不覆盖。管理员查看本厂按字段类型聚合的频次；报价员读不到其他厂的记录。用途是积累样本与迭代提示词/后处理，不是实时训练闭源提取引擎。

报价任务：轻量归集层，字段只有名称、客户名称、创建时间与创建人。零件图通过可空的 `quote_task_id` 归入，一张图同时最多属于一个任务，也可以不属于任何任务。历史检索按客户名称、创建时间、以及由成员零件图复核状态推导的进度（无零件图 / 复核未完成 / 已复核）。任务本身没有金额字段，也没有审批或状态流转。

报价底稿导出：`GET /quote-tasks/{id}/quote-sheet?format=xlsx|csv`。每个零件一行。列与顺序读该工厂 `quote_sheet_templates` 行（没有则用默认底稿）。模板是 onboarding 后台配置，没有 HTTP 写入入口，管理员界面也没有字段映射。导出必须带风险标签、非目标族的「实验性、不保证」、以及票 05 的低质量图标记。任务里还有未复核零件图时返回 409：自己能看见的会点名文件名；若未复核的零件不由当前报价员处理，则只报数量、不泄漏他人文件名。未复核检查针对任务里的全部零件，与调用者的 owner 可见性无关。

## 报价底稿模板 CLI（团队工具，不是产品功能）

onboarding 时由团队按该厂现有底稿写入列模板。不要把它做成管理员配置页，也不要加 HTTP 写入。走领域校验（未知源字段 / 空标题 / 重复列会被拒绝）。

```bash
cd backend
# 查看（没有写入则显示默认列）
QA_DATABASE_URL=postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant \
  PYTHONPATH=src uv run python -m quote_assistant.interface.cli.quote_sheet_template \
  show --factory-name 华东精密

# 写入 / 更新。JSON 数组，每项 {"source_key": "...", "header": "..."}
QA_DATABASE_URL=postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant \
  PYTHONPATH=src uv run python -m quote_assistant.interface.cli.quote_sheet_template \
  save --factory-name 华东精密 --columns-file ./templates/huadong.json

# 也可以逐列指定
QA_DATABASE_URL=postgresql+psycopg://quote:quote@127.0.0.1:5432/quote_assistant \
  PYTHONPATH=src uv run python -m quote_assistant.interface.cli.quote_sheet_template \
  save --factory-id 00000000-0000-0000-0000-000000000000 \
  --column part_name:品名 --column drawing_no:本厂图号 --column risk_labels:加工风险
```

可用 `source_key` 见 `QUOTE_SHEET_SOURCE_KEYS`（`drawing_no` / `part_name` / `material` / 关键尺寸 / 技术要求 / `risk_labels` / `experimental_mark` / `low_quality_mark` / `original_filename`）。漏配风险标签、实验性、低质量图三列时，导出仍会补在末尾。

## 缝 1 测试

pytest + FastAPI ASGI 测试客户端（不起端口）。启动时对真实 Postgres 执行 Alembic。

有 Docker 时默认用 testcontainers 拉起 `postgres:16`；CI 则用 workflow 里的 Postgres service，并设置 `QA_TEST_DATABASE_URL`。

```bash
cd backend
uv run pytest -m "not vendor_contract"
# 供应商契约测试（票 02 关闭后手工跑；默认 CI 不执行）：
# uv run pytest -m vendor_contract
```
