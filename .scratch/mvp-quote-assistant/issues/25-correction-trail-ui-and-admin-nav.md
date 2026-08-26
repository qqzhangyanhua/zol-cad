# 25 — 复核留痕界面与管理员页面的导航入口

**What to build:** 两处"后端做完了、前端没接上"的缺口。

## 一、修正记录在界面上不存在（用户故事 41）

用户故事 41 要求"在标记「已复核」之后仍能重新打开修改，**同时留下改动痕迹**，以便纠错不需要推倒重来"。

重开按钮有（`ReviewProgress`），**修正记录**实体、API、BFF 代理路由也都有——但 `app/api/part-drawings/[id]/correction-records/route.ts` 在全仓库里**没有任何组件调用它**。

所以现在的实际情况是：**报价员**重开一张已复核的图改了个尺寸，改动确实保留在结果里、也确实写了一条**修正记录**，但他在界面上看不到"这个字段原来是什么、谁在什么时候改成了现在这个值"。票 09 的 Comments 承认过这点（当时说"改动留痕指改动保留在结果里，不写修正记录实体"），但票 10 之后后端已经有了实体，前端没跟上。

**管理员**那边只有 `/admin/correction-stats` 的按字段类型聚合频次（用户故事 59），看不到单张图的明细。用户故事 40「已复核后成为可追溯的报价依据，以便事后出问题能查到当时确认的是什么」也指向同一个缺口——事后追溯需要看得到改动序列。

放在**零件图**详情页里合适，默认收起（大多数时候没人关心），展开后按时间倒序列出：字段、字段类型、原值 → 新值、操作人、时间。补录的项原值为空，这个后端已经处理好了。

## 二、两个已完工的管理员页面没有导航入口

`/admin/processing-records`（全厂处理记录，用户故事 53）和 `/admin/confidentiality`（保密说明，用户故事 61）都完整实现了，但 `AppSidebar` 只有 4 个管理员入口，这两个页面**不在其中**。

有意思的是「本厂数据」那一项的 `match` 函数把这三个路径都算作"高亮本项"，说明作者的意图是三者共用一个入口，但既没做二级导航、也没在 `/admin/tenant-data` 页面里放指向另两个页面的链接。全仓库 `href=` 的命中里没有一处指向这两个路径。

结果是**管理员只能手输 URL** 才能看到全厂记录和保密说明。用户故事 61 的场景是"管理员回答他自己客户的保密质询"——这是个会在客户电话里发生的动作，藏在无入口的 URL 后面等于没有。

顺带一处相关的文案问题：`ConfidentialityNotice` 的标题是「票 02 / ADR-0009 现状」，还展示了 `adr_path` 与 `research_notes_path` 两个仓库内文件路径；`RiskRuleCatalog` 的说明里写着「阈值仍是暂定值，不是票 01 样本结论」。把内部票号和 `.scratch` 路径摆给工厂管理员（以及他的客户）看，可信度是负的。这些字段是后端下发的，但决定展示什么、怎么措辞是前端的事。诚实是对的（ADR-0005 要求对保密现状诚实），但诚实不需要暴露我们的 issue tracker。

**Status:** claimed

- [x] **零件图**详情页能看到该图的**修正记录**：字段、字段类型、原值 → 新值、操作人、时间，按时间倒序
- [x] 默认收起，不干扰**复核**主流程
- [x] 未发生过修改的图显示明确的空态，而不是空白区域
- [x] `/admin/processing-records` 与 `/admin/confidentiality` 有可点击的导航入口
- [x] 管理员面向客户的保密说明里不出现内部票号、ADR 编号、`.scratch` 路径；诚实的内容保留，内部标识换成对外可读的表达
- [x] `RiskRuleCatalog` 的阈值说明同样去掉票号，保留"阈值为暂定值"这个诚实的事实

## Comments

- 2026-08-26: 落地票 25。PR：https://github.com/qqzhangyanhua/zol-cad/pull/23 （ready）

  设计：
  - 零件图详情并行拉 `GET /part-drawings/{id}/correction-records`，`CorrectionTrail` 放在复核工作台下方，`<details>` 默认收起。展开后按 `occurred_at` 倒序：字段（优先用提取字段 label）、字段类型、原值 → 新值、操作人、时间。补录原值为空显示「（空）」。无记录时展开是明确空态，不是空白。管理员打开详情时再读本厂账号表，把 `actor_user_id` 解成用户名；报价员没有账号列表接口，显示「账号」+ id 前 8 位。
  - 侧栏给「全厂处理记录」「保密说明」各加一项可点入口。「本厂数据」的 `match` 不再把另外两个路径算进同一高亮。没有做二级导航：电话里找保密说明需要顶层入口，共用一项会继续藏起来。
  - 对外文案只改前端展示。`presentConfidentialityNotice` 不渲染 `adr_path` / `research_notes_path`，票号和 ADR 编号换成「供应商已选定 / 尚未选定」等对外说法；待填、出筛集合为空、不训练/DPA 未落实这些诚实事实留下。`RiskRuleCatalog` 导语去掉「票 01」；规则 `description` 里后端下发的「ADR-0007 示例，待票 01 调研确认」也在展示层换成「暂定规则，待本厂真实样本核定」。后端 JSON 没改。

  验证：
  - 前端 `tsc --noEmit`、`pnpm lint` 通过。
  - 缝 1：`tests/test_confidentiality.py` + `tests/test_correction_records.py` 共 12 passed（含源码断言：详情页接上修正记录、侧栏有两个 href、客户文案不含票号/ADR/`.scratch`）。本环境无 Docker，用本机 Postgres + `QA_TEST_DATABASE_URL` 跑的。
  - 浏览器（admin_a）：侧栏能点进 `/admin/processing-records`（看到 FX-TQ-01.png / EMPTY-TRAIL.png）和 `/admin/confidentiality`。保密页页内查找「票 01」「ADR-」「.scratch」均为 0。FX-TQ-01 详情默认收起「3 条 · 展开查看」，展开后最新在前：最深孔（空）→ Ø8×48、图号 FL-001 → FL-009、最严公差 IT7 → IT6，操作人 `quoter_a`。EMPTY-TRAIL 展开后是「这张零件图还没有修正记录…」。偏好页导语与四条规则描述均无票号/ADR。
  - 未做报价员账号下列表里点一遍（报价员看不到管理员入口；修正记录详情用同一组件）。未改 26+。
  - CI `seam-1 / frontend` 与 `backend` 都 SUCCESS。PR MERGEABLE。
