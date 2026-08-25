# 01 — 目标零件族样本调研框架

**对应票：** `.scratch/mvp-quote-assistant/issues/01-target-part-family-research.md`  
**约束 ADR：** [ADR-0008](../../../../docs/adr/0008-focus-on-one-target-part-family.md)  
**框架状态：** 模板已就绪；结论 / 族类选定 / 阈值 / 标注均 **待真实样本**（blocked）

本目录只放调研产出与填空模板，不含应用代码、测试或虚构样本数据。

## 硬约束（不可违反）

1. **不凭空选定目标零件族** — 必须由 2~3 家目标工厂真实零件图样本的分布决定（ADR-0008）。
2. **不编造数量、比例、阈值或标注结果** — 表格里凡标 `待真实样本` 的格子一律留空或写该标记，禁止填入猜测值。
3. **风险规则阈值**在样本到位前不得定稿；ADR-0007 中的「公差 ≤ IT6」「孔深/孔径 > 5」等仅为规则*格式*示例，不是本调研已确认的阈值。

## 产出清单

| # | 文件 | 用途 | 可填状态 |
|---|------|------|----------|
| 1 | [01-sample-inventory.md](./01-sample-inventory.md) | 样本库存登记（来源厂、介质、页数、族类粗标） | 模板就绪，行内容待真实样本 |
| 2 | [02-family-distribution.md](./02-family-distribution.md) | 族类分布统计表 + 选定结论栏 | 统计与结论 **blocked** |
| 3 | [03-critical-dimensions.md](./03-critical-dimensions.md) | 选定族的关键尺寸类型清单 | 清单 **blocked**（依赖族类选定） |
| 4 | [04-risk-label-rules-draft.md](./04-risk-label-rules-draft.md) | 风险标签规则草案（条件 + 阈值） | 阈值 **blocked** |
| 5 | [05-fixture-atlas.md](./05-fixture-atlas.md) | Fixture 图集槽位（质量档 × 目标/非目标族） | 槽位定义就绪，入图与标注 **blocked** |
| 6 | [annotations/](./annotations/) | 人工标注期望提取结果模板 | 模板就绪，填写 **blocked** |

辅助目录：

- `samples/` — 真实零件图落盘处（本仓库不提交客户图纸时，在此放路径索引或 `.gitkeep`；实际文件可外置并在库存表里写路径）。
- `annotations/fixtures/` — 每张 fixture 一份标注副本的存放处。

## 执行顺序（样本到位后）

1. 收集 2~3 家厂的真实零件图，登入 `01-sample-inventory.md`（数量需足以看出分布，不是三五张）。
2. 按族类粗标并汇总到 `02-family-distribution.md`，**再**填写选定族与理由。
3. 针对选定族填写 `03-critical-dimensions.md`。
4. 针对选定族起草 `04-risk-label-rules-draft.md`（每条：判定条件 + 阈值）。
5. 从样本中挑 fixture，填满 `05-fixture-atlas.md` 各槽位，并为每张图按 `annotations/_TEMPLATE.md` 做人工标注。
6. 将结论回写 ADR-0008（或新开 ADR）；本框架不代替该步骤。

## 当前 blocked 项

- [ ] 真实样本收集与入库
- [ ] 族类分布统计数字
- [ ] 目标零件族选定与理由
- [ ] 关键尺寸清单定稿
- [ ] 风险规则阈值定稿
- [ ] Fixture 入图与质量档标定
- [ ] 人工标注期望提取结果
- [ ] ADR-0008 结论回写（选定族）
