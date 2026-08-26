# 21 — 提取引擎输出契约：提示词必须要求校验器强制的那些字段

**What to build:** 让提示词正文与适配器边界的校验规则说同一件事。现在这两边互相矛盾，真实多模态大模型接上的那一刻，**每一张零件图都会校验失败进「提取失败」**。

`EngineResultPayload` 用 `extra="forbid"` 强制要求 payload 恰好含三个 key：`quality_grade`、`is_assembly_or_exploded`、`fields`；`EngineFieldPayload` 再要求每个字段的 `key` 必须落在 `CANONICAL_FIELD_BY_KEY` 里、`label` 与 `category` 必须与字段目录逐字一致。

而两份提示词正文（`prompt_templates.py`）说的全部内容是「请提取标题栏、关键尺寸与技术要求；图上没有的字段留空」。它没有：

- 要求返回 JSON，也没给 JSON 结构；
- 提到 `quality_grade` 这个概念，更没说三档的取值是「清晰 / 一般 / 差」；
- 提到 `is_assembly_or_exploded`；
- 给出任何字段 key 列表（`drawing_number`、`material`、`tightest_tolerance`…）或对应的 `label` / `category`。

严格校验本身是对的（spec 明确要求"模型会编造字段、会给出类型不对的值，Pydantic 把这层校验放在适配器边界上"）。问题是契约只写在了校验器一侧，没有写进提示词。

这条连带暴露了两个更大的窟窿：

**图纸质量分级没有任何判定逻辑。** `domain/quality.py` 里只有三档枚举和四条展示文案，`quality_grade` 完全照抄引擎 payload。fixture 引擎按文件名硬查表返回，所以缝 1 一路绿灯。真实引擎上线时，如果提示词不要求模型评估图纸可读性，"差图劝退"这条分支（用户故事 6、7，ADR-0002 的半个信任模型）永远不会触发——而 spec 的问题陈述里写着"约一半是扫描件、手机拍照、微信截图"。

**装配图/爆炸图判定同样没有逻辑。** `status_after_grade` 只读 `result.is_assembly_or_exploded`，而提示词里根本没有一句话要求模型判定这个。用户故事 9「上传的是装配图或爆炸图时被明确告知不在处理范围，以便我不浪费时间等一个注定错的结果」在真实图上等于不存在。

**处理方式**：把输出契约写进提示词，并让契约只有一个来源。字段 key / label / category 已经在 `CANONICAL_FIELD_BY_KEY` 里了，提示词正文应当**由这份目录生成**而不是手抄一遍——两处手写必然漂移。分级与装配图判定作为提示词里的显式指令，取值范围与 `QualityGrade` 枚举、布尔语义对齐。

同时给校验失败留一条可诊断的路：现在 `parse_engine_result` 把所有 `ValidationError` 压成一句"未通过适配器校验"，`from exc` 保住了 traceback，但没有日志配置（见票 27）意味着生产上看不到任何东西。换供应商或调提示词时，这是唯一能告诉你"模型到底返回了什么"的地方。

**Status:** claimed

- [x] 提示词正文包含完整输出契约：JSON 结构、三个必需 key、字段 key / label / category 列表
- [x] 字段目录只有一份来源，提示词里的字段清单由 `CANONICAL_FIELD_BY_KEY` 生成，不手抄
- [x] 提示词显式要求模型给出**图纸质量分级**，取值与 `QualityGrade` 三档一一对应
- [x] 提示词显式要求模型判定是否为装配图 / 爆炸图
- [x] 提示词显式要求"图上没有的字段留空"，且留空的表达方式与校验器接受的形式一致（`null` 或 `""` 二者择一并写明）
- [x] 有一个测试用"符合提示词契约的样例 payload"打进 `parse_engine_result` 并通过——即校验器与提示词的一致性被测试锁住，而不是靠人读两个文件比对
- [x] 校验失败时留下足以定位的诊断信息（模型原始返回的结构摘要），但不落图像内容
- [x] 缝 1 既有测试全部不改仍然通过

## Comments

- 2026-08-26：落地票 21。PR：https://github.com/qqzhangyanhua/zol-cad/pull/19

  设计：
  - 契约单源在 `domain/engine_output_contract.py`。字段清单遍历 `CANONICAL_FIELD_BY_KEY`，三档取值遍历 `QualityGrade`。两份提示词（专用占位 / 通用实验性）只拼前缀，正文契约不再手抄。
  - 留空约定：**JSON `null`**。写在契约常量 `ENGINE_ABSENT_FIELD_VALUE` 与提示词里。校验器仍接受 `""` 并归一为 `None`（原行为未改），提示词不要求空字符串。
  - 分级与装配/爆炸图：提示词里是显式判定指令，取值与 `QualityGrade` / 布尔语义对齐。领域层仍是「照抄引擎 payload」——本票只把判定写进模型合同，不另做程序化分级器。fixture 引擎仍按文件名硬查表，缝 1 路径不变。
  - 校验失败：对外原因仍是「提取引擎返回结果未通过适配器校验，脏数据未进入领域层」（缝 1 原断言未改）。结构摘要挂在 `ExtractionValidationFailed.diagnostic`，并打 `engine_payload_validation_failed` 日志。摘要只记 key / 类型 / 错误 loc，不落 `image_base64` / `page_content` 等内容。Alembic `fileConfig` 会 mute 导入期 logger，发射前会重新打开该 logger；正式 `basicConfig` 仍归票 27。

  未做票 22+（不合并两次引擎调用）。族类专用取数策略仍等票 01。

  验证：
  - `QA_TEST_DATABASE_URL` 指向本机 Postgres 16：`uv run pytest -m "not vendor_contract"` → **145 passed / 1 deselected**。既有缝 1 文件未改。
  - 新测试锁一致性：`engine_output_contract_example()` 与提示词正文里的 JSON 样例打进 `parse_engine_result` 均通过；目录字段与 `QualityGrade` 三档都出现在两份正文里。
  - 本票无前端 / UI 改动，未做浏览器验证。
