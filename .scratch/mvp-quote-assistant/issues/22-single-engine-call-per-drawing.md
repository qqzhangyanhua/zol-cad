# 22 — 一张零件图只调一次提取引擎

**What to build:** 把**图纸质量分级**与**读图取数**合并成对提取引擎的单次调用。现在一张图至少调两次，差图"仍然继续"是三次——真实多模态大模型上，成本和延迟直接翻倍。

`apply_grading` 调 `engine.extract()` 拿到一个完整的 `ExtractionResult`，然后**只取 `quality_grade` 和 `is_assembly_or_exploded` 两个值，把 `result.fields` 整个丢掉**。紧接着 `ProcessPartDrawing.execute` 调 `apply_extraction`，后者再调一次 `engine.extract()` 拿字段。`ContinueDespitePoorQuality` 走的还是 `apply_extraction`，所以差图被显式覆盖继续时是第三次。

每次调用还各自把原图从对象存储取一遍、PDF 选定页栅格化一遍（`build_extraction_request`）。

这个结构在缝 1 里毫无痛感——fixture 引擎瞬时返回，调两次和调一次的测试表现完全一样。所以它一直没被发现。但 spec 在成本约束一节明确写着"上传限制单文件大小与 PDF 页数上限（控 API 调用成本）"，一边掐上传限制一边把每张图的调用翻倍，是自相矛盾的。

分级信号本来就和字段在**同一份 payload** 里（`EngineResultPayload` 三个 key 一起返回，见票 21），所以合并不需要新的引擎能力，只是别把已经拿到的数据扔掉。

**要保住的两个性质**：

1. **分级先落库、再进取数。** `ProcessPartDrawing` 的 docstring 说明了理由：分级 commit 在取数开始之前，否则**报价员**会一直卡在「分级中」看不到分级结果。合并调用后仍要保留"先写分级、再写字段"的两次状态迁移与两条事件，只是它们共用同一次引擎返回。
2. **分级失败要从分级重试，不能跳过劝退直接取数。** 现在靠 `drawing.quality_grade is None` 判断，合并后这个判断依然要成立。

**差图分支怎么办**：分级为「差」时进 `建议人工`，此时字段其实已经拿到了但不应该预填（用户故事 6「不硬给我一份看起来很自信的错结果」）。**报价员**显式覆盖继续后，应当复用第一次调用已经拿到的字段，而不是再调一次。这需要把首次调用的结果暂存下来。如果暂存的复杂度不划算，退一步的做法是：分级为「差」时不暂存、覆盖继续时重新调用一次——那也只是把三次降到两次，仍然比现在好，但要在票里写清选了哪条。

**装配图 / 爆炸图分支**同理：判定为超出范围时字段直接丢弃，不需要暂存，因为这条分支没有"覆盖继续"的入口。

**Status:** claimed

- [x] 一张图从上传走到「已提取」，对 `ExtractionEngine.extract` 的调用次数为 1
- [x] 原图取回与 PDF 选定页栅格化在一次处理里也只做一次
- [x] 分级结果仍先落库并 commit，**报价员**在取数期间能看到已分级状态
- [x] 分级本身失败时重试仍从分级开始，不跳过劝退分支
- [x] 差图被显式覆盖继续时不产生额外的引擎调用（或在票里写明为何选择重新调用）
- [x] 缝 1：用计数型假引擎断言单张图的调用次数，这个不变量被测试锁住而不是靠人读代码
- [ ] 缝 1 既有测试全部不改仍然通过

## Comments

- 2026-08-26：落地票 22。PR：https://github.com/qqzhangyanhua/zol-cad/pull/20

  **差图选了暂存复用，不重调。** 分级成功后把字段写入 `part_drawings.stashed_extracted_fields`（清晰/一般也写，给分级 commit 与取数写入之间的崩溃/滞留一条不重调的路）。`apply_extraction` 见到暂存就直接预填并清空暂存，不再 `fetch` / 栅格化 / `extract()`。建议人工时 `extracted_fields` 仍为空，API 不预填。装配图 / 爆炸图 `fields_to_stash_after_grade` 返回 `None`，字段丢弃。已提取后再点重试没有暂存，会再调一次引擎——那是一次新的处理，不是本票要消掉的双调用。

  两次状态迁移 + 两次 commit 保留：`apply_grading` commit 之后 `quality_grade` 已可见，再 `apply_extraction`。事件仍是 已上传 → 分级中 → 已分级 → 提取中 → 已提取。分级失败 `quality_grade is None`，重试仍进 `apply_grading`，不会跳过劝退。

  渲染端口挂到 `app.state.drawing_page_renderer`，与引擎 / 对象存储一样可被缝 1 替换，计数测试才能锁栅格化次数。

  **既有测试不能「全部不改」。** 票里写「双调用在缝 1 毫无痛感」不成立：`test_extraction.py` 里 `_FirstOkThenDirtyEngine` 把「第一次成功、第二次脏」编码成产品行为（分级过了、取数校验失败）。合并后只有一次 `extract()`，脏 payload 在分级阶段就失败，`quality_grade` 仍是 `None`，重试从分级开始。这三条测试改成 `_AlwaysDirtyEngine`，事件序列从「已分级 → 提取中 → 提取失败」改为「分级中 → 提取失败」；产品断言（脏数据不进领域层、可重试、重试仍失败不写编造字段）没放宽。另外 `test_启动时真实执行了Alembic迁移` 把 head 从 `0011` 钉到 `0012`——加列就必须改这一行。其余既有缝 1 文件未改。

  未做票 23+。

  验证：
  - `QA_TEST_DATABASE_URL` 指向本机 Postgres 16：`uv run pytest -m "not vendor_contract"` → **149 passed / 1 deselected**。
  - 新测试 `test_single_engine_call.py` 用计数型假引擎 / 存储 / 渲染器锁：清晰图 1 次 extract+fetch+render；差图仍然继续仍是 1 次且字段来自暂存；装配图 1 次后丢弃字段；分级失败后重试从分级再走一遍。
  - 本票无前端 / UI 改动，未做浏览器验证。
