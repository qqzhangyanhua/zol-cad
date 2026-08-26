# 18 — 提取输入栅格化：PDF 选定页真正送进引擎

**What to build:** 让送进**提取引擎**的东西真的是"**报价员**指定的那一页的图像"。现在 `apply_extraction` 是把对象存储里的原始字节直接丢给引擎——PDF 传的是整个 PDF 文件，`selected_page` 在提取路径上完全没生效。假引擎按文件名查预置结果，所以这个缺陷被完全掩盖；换成真实多模态大模型的那一刻它就会暴露成"选了第 3 页却按第 1 页取数"，或者干脆调用失败。

票 04 的用户故事 4 已经承诺"多页 PDF 时明确知道系统只处理我指定的那一页（默认第 1 页），以便结果和我的预期一致"。上传界面照这个承诺收了页码、也落了库、也在详情里回显，但**这个承诺在取数环节没有兑现**。

**这一票不选供应商、不调用任何付费 API。** 它补的是票 17 真实实现落地前必须先有的输入通路。

**Blocked by:** None（与票 02 供应商选型无关，可先做）

**Status:** claimed

- [x] 新增**页面渲染** Port：输入是原始字节、媒体类型、选定页码，输出是交给提取引擎的单页内容与其媒体类型
- [x] PDF 按 `selected_page` 栅格化为图像；图片原样透传，不做无谓重编码
- [x] 上传后的分级调用与 `apply_extraction` 的取数调用**走同一条渲染通路**，不允许其中一条绕过
- [x] 渲染失败（页码越界、PDF 损坏）映射为**提取失败**并保留重试路径，脏数据不进领域层
- [x] 用例层与领域层不出现任何 PDF 库名，渲染实现只活在适配器层
- [x] 缝 1：上传一份两页 PDF 并指定第 2 页，断言引擎收到的是第 2 页的内容而不是第 1 页
- [x] 缝 1：PDF 进入引擎时媒体类型是图像；图片上传时内容与媒体类型原样透传

## Comments

- Port `DrawingPageRenderer` 在 `usecase/ports.py`，产物类型 `RenderedPage` 在 `domain/extraction.py`。适配器
  `adapter/pdf/renderer.py` 用 pypdfium2 渲染，200 DPI（PDF 默认 72 DPI 对工程图上的尺寸小字不够看），
  最长边 4000 px 封顶，避免 A0 大图渲成没有供应商肯收的巨图。
- 统一入口是 `build_extraction_request`：分级、取数、差图仍然继续三条路径都从这里构造 `ExtractionRequest`。
  `test_layering` 新增一条断言——`usecase/` 下除它以外任何地方出现 `ExtractionRequest(` 即判定为绕过渲染通路。
- 渲染失败新增 `PageRenderFailed`，继承既有的 `ExtractionEngineFailed`，因此自动复用「提取失败 → 重试」路径，
  用例层一行没改。
- **上传阶段的分级调用如果渲染失败仍会让整批上传失败并回滚**，与今天分级阶段引擎异常的行为一致。这条留给票 19：
  分级挪进后台作业之后，单张失败才谈得上不影响同批其他图。
- 验证：缝 1 `uv run pytest -m "not vendor_contract"` 135 passed / 1 deselected（新增 3 条 + 1 条分层断言）。
  本机无 Docker，用 `postgresql@14` 在 55432 起了一个独立实例跑真实 Postgres，未动用户已有的 5432。
