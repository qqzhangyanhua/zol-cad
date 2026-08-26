# 29 — 回填票 01 的调研结论：零件族判定与风险阈值

**What to build:** 票 01（目标零件族样本调研）关闭之后，把结论真正接进代码。现在有两处占位在真实图纸上会直接失效——它们都被诚实地标注了，但标注不等于能用。

## 一、零件族判定靠文件名子串匹配

```
def classify_part_family(input_drawing_id: str) -> str:
    haystack = input_drawing_id.upper()
    if _TARGET_FIXTURE_SLOT in haystack:      # "FX-T"
        return TARGET_PART_FAMILY_ID
    if _NON_TARGET_FIXTURE_SLOT in haystack:  # "FX-N"
        return PROVISIONAL_OTHER_PART_FAMILY_ID
    return UNKNOWN_PART_FAMILY_ID
```

传进去的是**客户上传的原始文件名**。真实工厂的文件名不会含 `FX-T`，所以每一张真实图都落 `unknown`：

- 全部走通用实验性提示词 → 用户故事 20「当这张图属于**目标零件族**时，我想系统用针对该族的方式来取数，以便准确率更高」在生产上不生效。
- 全部带「实验性、不保证」标记，并且这个标记会一路进到**报价底稿**里（用户故事 48）。于是**每一行**都写着"需要更谨慎"，标记本身就失去了区分度——用户故事 21 的意图是让非目标族的行显眼，全都显眼就等于都不显眼。

族类判定需要基于**图纸内容**（零件名称、关键尺寸的形态特征、或直接让引擎在提取时给出族类判断）。这个决定依赖票 01 选定的是哪一族——车削回转体和 CNC 铣削棱柱件的判据完全不同。

顺带一个安全性副作用：fixture 引擎也用文件名子串查表（`fixtures.py`）。任何人把文件命名成 `我的图-FX-TQ-01.pdf` 就能拿到一整套预置的假提取结果（图号 FL-001、材料 45#、IT7…）。开发期无害，但这是"假数据能从生产入口进来"的一条路径，而且没有任何开关能在生产环境禁掉 fixture 引擎。真实引擎接上后应当把 fixture 引擎限制在非生产环境。

## 二、风险规则阈值是为了接线编出来的

四条阈值全部标了 `PROVISIONAL_`，其中两条明确写着"invented only to wire the engine"：

| 常量 | 值 | 出处 |
| --- | --- | --- |
| `PROVISIONAL_IT_GRADE_MAX` | IT6 | ADR-0007 里点名的例子 |
| `PROVISIONAL_DEPTH_TO_DIAMETER_GT` | 5 | ADR-0007 里点名的例子 |
| `PROVISIONAL_THIN_WALL_MM_MAX` | 2 mm | 编的 |
| `PROVISIONAL_SLENDERNESS_GT` | 10 | 编的 |

规则引擎本体是好的——纯函数、封闭词表、缝 2 的表驱动测试加两条不变量测试都在。**要换的只是触发标准**，机制不动。

这件事的紧迫性在于用户故事 22 的动机：「以便我在定价时不漏掉加工难点」。阈值定错的后果是双向的——太松会漏掉真该上浮的件（就是 spec 问题陈述里那个"漏掉一个 IT6 的严公差就亏本干活"），太紧会让**报价员**被误报淹没然后开始忽略所有标签，那时标签就等于不存在了。这个平衡只能用真实样本调出来。

`RiskRuleCatalog` 现在向**管理员**如实说明了"阈值仍是暂定值"（这点做得对，见票 25 关于去掉票号的部分）。回填之后这句话要改掉，否则管理员会一直不信任它。

## 三、提示词正文

`prompt_templates.py` 的两份正文都是自述占位（"本模板仅占位"）。票 21 会把输出契约写进去，但**族类专用的取数策略**——针对车削件该重点找什么、针对铣削件该重点找什么——要等票 01 的结论。这是"专用模板"能提高准确率的全部实质内容。

**Blocked by:** 01（目标零件族样本调研）

**Status:** ready-for-agent

- [ ] 零件族判定基于图纸内容而非文件名
- [ ] 真实工厂图纸能被正确分到目标族 / 非目标族，不再全部落 `unknown`
- [x] fixture 引擎在生产环境不可用，文件名不再能触发预置的假提取结果
- [ ] 四条风险阈值替换为票 01 的样本结论，`PROVISIONAL_` 前缀与"编来接线"的注释一并去掉
- [ ] 缝 2 的表驱动用例按新阈值更新"刚好触发 / 刚好不触发 / 边界值"
- [ ] 两条不变量测试（无"安全/无风险"语义、同输入同输出）仍然通过
- [ ] 目标族专用提示词写入该族的取数策略，不再是占位文案
- [ ] `RiskRuleCatalog` 面向**管理员**的说明改掉"阈值为暂定值"
- [ ] ADR-0008 据此更新或关闭

## Comments

- 2026-08-26：票 01 仍是 `ready-for-human`，等真实工厂图纸。本轮**不编造目标零件族、不替换 `PROVISIONAL_` 阈值、不写车削/铣削取数策略、不关闭票 01、不改 ADR-0008、不把管理员规则说明改成「已定稿」**。本票未全部完成。

  **已落地（不依赖 01）：**
  - 复用票 27 的 `QA_APP_ENV` / `Settings.is_local`。非 `local` / `dev` / `development` / `test` 时：`validate_runtime_settings` 与 `build_extraction_engine` 都拒绝 `QA_EXTRACTION_ENGINE=fixture`；`FixtureExtractionEngine(allowed=False)` 也不能构造/extract。生产必须 `vendor`（票 02 未关时仍是未选定骨架）。
  - 文件名 `FX-T` / `FX-N` 槽位判定只在「本地且当前选了 fixture」时启用，供缝 1 使用。生产即使文件名叫 `我的图-FX-TQ-01.pdf` 也不会走假引擎、也不会被标成目标族。
  - 加了 `classify_part_family_from_content` / `adopt_content_classified_family` 钩子，提取后会调用；票 01 给出判据前一律 `unknown`，没有「看起来像轴」之类启发式。

  **仍等 01：** 内容判族真正生效、真实图纸不再全落 unknown、四条阈值与缝 2 边界、专用提示词策略、`RiskRuleCatalog` 去掉「暂定」、ADR-0008 更新或关闭。
