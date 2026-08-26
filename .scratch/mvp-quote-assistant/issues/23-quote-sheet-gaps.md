# 23 — 报价底稿补全：模板写入路径、CSV 入口、跨报价员导出漏洞

**What to build:** **报价底稿**这条链上有三个独立的缺口，其中一个是正确性 bug。

## 一、onboarding 模板没有任何写入路径

用户故事 46「我想导出的**报价底稿**长得就像我们厂现在用的那份表」是对客户的直接承诺，54a 与 spec 的实现决策把它的落地方式定成"onboarding 时由团队手工配好，不做用户自助的映射 UI"（服务代替功能）。

表、ORM 模型、领域校验、读取路径都齐了：`quote_sheet_templates` 迁移、`SqlQuoteSheetTemplateRepository`、`resolve_quote_sheet_template`。但 `QuoteSheetTemplateRepository.save_for_tenant` 在整个 `src/` 下**没有任何调用方**——没有 HTTP 入口（这是刻意的，管理员配置页里不该有这一项）、没有 CLI、没有 seed、没有迁移数据、没有 onboarding 脚本。唯一的调用在 `tests/helpers.py`。

结果是：所有工厂实际都只能拿到 `default_quote_sheet_template()` 的默认列。"服务代替功能"的前提是那个服务真的有工具可用；现在 onboarding 的人只能手写 SQL 往 JSONB 列里塞。

需要一个团队用的写入入口。CLI 最合适——它明确不是产品界面，不会被误当成用户功能，也能进版本库、能被 review。

## 二、CSV 导出在界面上不可达

后端支持 xlsx 与 csv 两种格式且都有测试覆盖，BFF 路由也读了 `format` 查询参数。但 `QuoteSheetExportButton` 把格式写死成 `format=xlsx`，按钮文案固定为「导出报价底稿 (Excel)」。票 14 的验收项写的是 xlsx / csv 两种。

## 三、跨报价员的未复核零件图能绕过导出拦截

`ExportQuoteSheet.execute` 里，owner 过滤发生在未复核检查**之前**：

先 `filter_owned_by_actor` 按 `uploaded_by_user_id` 收窄 `drawings`，再对收窄后的列表跑 `unreviewed_drawings_for_export`。

**管理员**可以把任意本厂**零件图**归入任意**报价任务**（`AssignPartDrawingToQuoteTask` 对管理员放行）。于是：管理员把报价员 C 上传的一张未复核的图归入报价员 A 的任务，A 去导出时那张图既不出现在导出行里、也不参与未复核拦截——导出成功、行数少一行、**没有任何警告**。

用户故事 49 的承诺是"在**报价任务**里还有未完成**复核**的零件时导出被拦下或至少被明确警告，以便我不会把半成品发出去"。现在这个承诺在最容易出问题的多人协作场景下静默失效。

修法的关键是想清楚语义：**报价任务**是归集层，任务里有哪些零件是任务的事实，不该因为看的人是谁而变化。倾向于"未复核检查针对任务里的全部零件，与 owner 过滤无关"——即先检查再过滤。如果这样会让 A 看到 C 的文件名（**报价员**默认只看自己的数据，用户故事 52），那警告文案里就不列文件名，只说"本任务中有 N 个零件尚未完成复核，其中部分不由你处理"。这比静默少导一行要诚实得多。

顺带：前端已经算出了 `unfinished` 并渲染了明确警告，但导出按钮的 `disabled` 只绑了 `pending`，不受 `unfinished` 影响。用户看完警告点下去，走一遍网络拿回 409 再变红字。警告已经说清楚了就别让用户再撞一次墙。

**Status:** claimed

- [x] 有一个 onboarding 用的 CLI 能为指定工厂写入 / 更新 / 查看**报价底稿**模板，走领域校验，不经过 HTTP
- [x] CLI 的存在与用法写进 `backend/README.md`，写明它是团队工具不是产品功能
- [x] 管理员配置页仍然没有模板这一项（这条不变量不能被这张票破坏）
- [x] 前端导出入口同时提供 xlsx 与 csv
- [x] 未复核拦截针对**报价任务**里的全部零件，不受调用者的 owner 可见性影响
- [x] 警告文案不泄漏其他**报价员**的文件名
- [x] 前端在存在未完成**复核**的零件时禁用导出按钮，用户不需要撞一次 409
- [x] 缝 1：管理员把 C 的未复核图归入 A 的任务后，A 导出被拦下；把该图复核完成后 A 能导出且行数正确
- [x] 缝 1：写入过模板的工厂导出的列与模板一致，未写入的工厂拿到默认列

## Comments

- 2026-08-26: 落地票 23。PR：https://github.com/qqzhangyanhua/zol-cad/pull/21

  设计：
  - onboarding CLI：`python -m quote_assistant.interface.cli.quote_sheet_template {show,save}`。走 `SaveQuoteSheetTemplate` / `GetQuoteSheetTemplate`，领域校验后调用 `save_for_tenant`。没有 HTTP 写入，管理员页没有模板项。用法写在 `backend/README.md`，标明团队工具。
  - 前端导出：`QuoteSheetExportButton` 同时提供「导出 Excel」与「导出 CSV」。
  - `ExportQuoteSheet` 先对任务里全部零件做未复核检查，再按 owner 过滤导出行。自己能看见的未复核仍点名文件名；有不可见成员时文案为「本任务中有 N 个零件尚未完成复核，其中部分不由你处理」。
  - 详情增加 `unreviewed_member_count`（按任务全员计算，不把他人文件名塞进 drawings）。前端用它禁用按钮，隐藏的未复核也不会先撞 409。
  - 复核完成后，A 导出的行数仍按 owner 可见性（A 自己的零件），不把 C 的提取结果写进 A 的表。这与「先检查再过滤」一致。

  验证：
  - 缝 1：`151 passed`（真实 Postgres + Alembic head `0012`，`QA_TEST_DATABASE_URL`）。含跨报价员 409 不泄漏文件名、复核后导出 1 行、CLI 写入后该厂列变、未写入厂仍是默认列；原有底稿 / 任务测试仍过。
  - 前端 `tsc --noEmit` 通过。eslint 仅有两处既有 unused warning（`quote-tasks/[id]/page.tsx` 的 `Link`、`AppSidebar.tsx` 的 `OverviewIcon`），不是本票引入。
  - 浏览器：任务详情 SSR HTML 两个按钮都带 `disabled`，警告列出自己的 `FX-TQ-01.png`。管理员 `/admin/preferences` 与 `/admin/accounts` HTML 不含「字段映射 / 导出模板 / source_key / 报价底稿模板」。复核完成后 API 导出 csv 1 行；CLI 写入华东精密模板后再导出 xlsx，表头为「品名 / 本厂图号 / 加工风险」加两列必带标记。
  - 未做票 24+。未加管理员模板映射入口。
