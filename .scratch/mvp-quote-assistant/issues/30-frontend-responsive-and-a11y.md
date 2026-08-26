# 30 — 前端响应式与无障碍

**What to build:** 一组体验缺口的合集。都不影响正确性，但会决定**报价员**愿不愿意每天用它。

## 响应式基本没做

`AppShell` 外层是 `h-screen overflow-hidden`，`AppSidebar` 是 `w-64 shrink-0`，没有 `hidden md:flex`、没有汉堡菜单、没有抽屉。375px 宽的手机上侧栏独占 256px，主内容区被压到约 100px 宽。

全仓库响应式断点的使用集中在少数几个组件里，**页面级布局（`AppShell` / `AppSidebar` / `AppHeader` / 所有 `app/**/page.tsx`）几乎为零**。

spec 的 Out of Scope 排除的是"移动端原生应用"，没有豁免响应式 Web。而**报价员**的真实工作场景里有一半图纸是"微信截图、手机拍照"（spec 问题陈述原话）——手机上打开看一眼状态是很自然的动作。至少要让侧栏可收起、主内容区在窄屏下可用。

并排**复核**页（用户故事 30）在窄屏下天然要变成上下堆叠而不是左右并排，这个需要单独设计一下——"同一个屏幕上左边表单右边原图"的价值在手机上不成立，堆叠 + 可折叠可能更合适。

## 缩放平移完全不可键盘操作

`ZoomPanViewport` 只绑 `onWheel` 与 `onPointer*`，容器没有 `tabIndex`、没有键盘事件。三个按钮可以 Tab 到（放大 / 缩小 / 重置），但**平移没有任何键盘替代**。

用户故事 31「我想能在原图区自由缩放和平移，以便我看清扫描件上的小字」——对键盘用户和辅助技术用户，这条现在只有一半可用。方向键平移是标准做法，成本很低。

## aria-label 覆盖率很低

只有 8 个文件共 10 处。没有可访问名称的包括：

- `AppHeader` 的返回链接（内容只有字符 `←`；`backLabel` prop 被声明、被两个页面传入，函数体里从未使用——见票 24）
- `ZoomPanViewport` 的放大 / 缩小 / 重置按钮
- `PartDrawingList` 行尾的 `→` 指示符
- `AppSidebar` 的 `›`

## 其他

- **重复 h1**：`/admin/correction-stats` 同时渲染 `AppHeader` 的 `<h1>字段修正统计与复核洞察</h1>` 和 `CorrectionStatsPanel` 的 `<h1>修正记录统计</h1>`。
- `RiskLabelList` 空态用了 `role="note"`，这不是标准 ARIA 角色，会被忽略。
- **假的组织切换器**：`AppSidebar` 在工厂名为空时回填「精密制造有限公司」，旁边的 `›` 强烈暗示可以切换组织。而这个产品的租户模型是一个用户属于一个工厂，跨厂切换根本不存在，用户故事 55 要求"我看不到其他工厂的任何数据"。租户名是保密边界的可见锚点，不该有假回填，也不该暗示一个不存在的越界动作。
- **编造的用户头衔**：`AppSidebar` 把管理员显示成「高级制造工程师 · 管理员」。权限模型只有**管理员** / **报价员**两档，「高级制造工程师」是凭空造的。
- `RiskLabelList` 空态文案前面加了个 `✓`。这个符号在界面别处专门表示"已通过 / 已确认"（`✓ 已确认`、`✓ 已保存`、完成态绿勾）。放在「未发现可判定的风险项，不代表此件无风险」前面，正好把 ADR-0007 要求"沉默不被读成安全"的那句话渲染成了一个通过标记——这是票 20 那类问题的一个小号版本，顺手一起改掉。
- `lib/types.ts` 953 行、60+ 个手写 `parseXxx` 运行时校验器。不违反组件行数规范（它不是组件），但已经到了可读性临界点，可按领域切分。

**Status:** claimed

- [x] 侧栏在窄屏下可收起，主内容区在 375px 宽下可用
- [x] 并排**复核**页在窄屏下有可用的堆叠布局
- [x] `ZoomPanViewport` 支持键盘平移与缩放
- [x] 图标按钮与纯符号链接都有可访问名称
- [x] 每页只有一个 h1
- [x] `RiskLabelList` 空态去掉 `✓`，改用不表达"通过"的中性呈现，且 `role` 用标准值
- [x] 工厂名不回填假值；侧栏不再暗示可切换组织
- [x] 不再显示编造的用户头衔，角色只显示**管理员** / **报价员**
- [x] `lib/types.ts` 按领域拆分

## Comments

- 2026-08-26: 落地票 30。PR：https://github.com/qqzhangyanhua/zol-cad/pull/28 （ready，CI 绿）

  设计：
  - 壳层：`AppShell` 管抽屉状态。`< md` 侧栏 `max-md:hidden` / 打开时固定抽屉 + 遮罩 + Escape + 导航点击关闭。`AppHeader` 汉堡按钮 `aria-label="打开导航"`。375px 主栏实测 351px，不再被 256px 侧栏挤没。
  - 复核：`PartDrawingWorkspace` 窄屏上下堆叠，表单 / 原图可分别收起；`lg+` 仍是左表单右原图。
  - `ZoomPanViewport`：原图区 `tabIndex={0}`，方向键平移、`+`/`-` 缩放、`0` 重置。按钮补 `aria-label`。
  - 票 24 的 `backLabel`（`aria-label` + `sr-only`）未改，详情页仍是「零件图列表」。`PartDrawingList` / `QuoteTaskList` 的 `→` 标 `aria-hidden` 并补 sr-only。侧栏去掉 `›`。
  - `/admin/correction-stats` 面板标题改 `h2`，页上只留 `AppHeader` 一个 h1。
  - `RiskLabelList` 空态去掉 `✓`，`role="status"`。摘要卡里同一句空态也改成 `status`（同一页、同一句 ADR-0007 文案）。`ExtractionDisclaimer` 仍是 `role="note"`，那是看图提示条，不是风险空态，没动。
  - 本厂名原样显示，空也不回填「精密制造有限公司」。角色只显示 **管理员** / **报价员**。
  - `lib/types.ts` 按领域拆到 `lib/types/{auth,part-drawing,risk,quote-task,factory,corrections,processing-time,confidentiality,api,guard}.ts`，`@/lib/types` 仍是桶导出。

  验证：
  - `pnpm exec tsc --noEmit` 与 `pnpm lint --max-warnings=0` 通过。
  - 本环境没有 Postgres / Docker，用本地 mock 后端 + 无头 Chrome（375×812）量过：侧栏关闭时 `display:none`、主栏 351px；抽屉里是「本厂 / 华东精密 / 报价员|管理员」，无 `›`、无假厂名、无编造头衔。
  - 复核页收起原图 / 表单后对应 pane `display:none`。键盘：方向键右两次 `translate(-80px)`，`+` 到 120%，`0` 回到 100%。
  - `/admin/correction-stats` 只有一个 h1：「字段修正统计与复核洞察」。
  - `lg` 桌面复核仍是左表单（448px）右原图（526px）。
  - CI `seam-1 / frontend` 与 `backend` SUCCESS。
