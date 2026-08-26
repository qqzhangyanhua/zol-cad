# 28 — 后端接入 lint 与类型检查

**What to build:** 给后端补上和前端对等的静态检查。现在两边不对称：前端有 `tsc --noEmit` + `eslint`（`no-explicit-any` 设为 error、`strict: true`），后端的 `pyproject.toml` 里没有 ruff 也没有 mypy，CI 的 backend job 只跑 pytest。

这个不对称有点讽刺：spec 明确把"所有值得测的行为都在后端"当作分层的理由，后端承载了全部领域逻辑，却是检查更松的那一边。

已经发现的一些征兆：

- `app.py` 的 import 顺序是乱的（`recover_stranded_part_drawings` 插在 routes 导入中间），ruff 的 isort 规则会直接管住。
- `_grading_failed` 没有返回类型标注。
- `_recover_stranded_part_drawings(session_factory)` 参数无类型标注。

这些都是小事，但正是因为小才需要工具管——人工 review 抓这类东西的性价比很低，而且会挤占 review 该关注的地方（领域不变量有没有被绕过）。

**类型检查对这个项目有个具体价值**：适配器边界的严格校验（票 21）与领域层的纯度是这套设计的两根支柱。mypy 能在编译期抓住"某个用例层函数悄悄接受了 `Any`"这类漂移——`test_layering.py` 已经用导入检查守住了分层，类型检查是它的补充。

**分层检查已经有了，不要重复。** `test_layering.py` 用禁止导入清单守住 domain / usecase 不碰 fastapi / sqlalchemy / oss2 / pypdf / openpyxl，还断言了几条更细的不变量（用例层不得自建 `ExtractionRequest`、调用点不得内联提示词正文、报价任务不得出现 `amount` / `price` / `approval`）。这些是项目特有的规则，工具管不了，保留原样。

**落地方式**：先把工具接进来并让它在现有代码上通过（必要时用配置收窄严格度，而不是靠满地 `# type: ignore`），再在 CI 里加成必过项。ruff 的 format 是否启用需要一个决定——如果启用，就在同一个 commit 里一次性 format 全库，别让它和后续功能改动混在一起。

**Status:** claimed

- [ ] `pyproject.toml` 里配好 ruff（lint + isort），规则集与项目风格匹配
- [ ] `pyproject.toml` 里配好 mypy，严格度写明并有理由
- [ ] 现有代码全部通过，不靠散落的 `# type: ignore` 蒙过去
- [ ] CI 的 backend job 跑 lint 与类型检查，且是必过项
- [ ] `backend/README.md` 写明本地怎么跑这两项
- [ ] 若启用 ruff format，全库格式化独立成一个 commit
- [ ] `test_layering.py` 的项目特有规则保留，不被工具替代

## Comments
