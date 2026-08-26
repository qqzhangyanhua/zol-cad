# 24 — 前端错误态与加载态，以及把 lint 修回绿

**What to build:** 三件收尾的事：CI 现在是红的、后端一挂前端就白屏、`globals.css` 里有 122 行手写 CSS 违反项目规范。

## 一、CI 在 main 上是红的

`.github/workflows/seam-1.yml` 的 frontend job 跑 `pnpm exec tsc --noEmit` 和 `pnpm lint`。本地 `pnpm lint` 当前 **1 error + 9 warnings，exit code 1**：

```
CadDrawingReviewSummary.tsx
  55:7  error  Compilation Skipped: Existing memoization could not be preserved
         react-hooks/preserve-manual-memoization
```

`useMemo` 依赖 `currentPrice`，而它派生自渲染期重建的可变对象 `batchPrices`，React Compiler 因此拒绝优化整个组件。票 19 的验证记录里只写了「前端 `tsc --noEmit` 通过」——lint 没跑，所以这个 error 溜进了 main。

这个 error 会随票 20 删掉伪造的定价逻辑一起消失。剩下 9 条 warning 是未使用的导入与变量，其中 `AppHeader` 的 `backLabel` 未使用同时是一个无障碍缺陷（返回链接的内容只有字符 `←`，屏幕阅读器只念得到这个；`backLabel` 被声明、被两个页面传入，函数体里却从未使用）。

## 二、没有任何错误态与加载态

`src/app` 下只有两个 `not-found.tsx`，**没有一个 `error.tsx`、`loading.tsx` 或 `global-error.tsx`**。所有页面在后端返回非 2xx 时直接抛异常：

```
if (!meResponse.ok || !listResponse.ok || !tasksResponse.ok) {
  throw new Error("无法读取零件图列表");
}
```

这个模式出现在全部 10 个页面。生产构建下用户看到的是 Next.js 默认的 "Application error: a client-side exception has occurred"：没有说明、没有重试入口、没有返回路径。后端宕机、502、或数据库连接断开时，整个应用是白屏级体验。

同时因为没有 `loading.tsx`，页面全是 SSR 阻塞——**零件图**详情页并行发 5 个后端请求，期间浏览器完全无反馈。

这件事在真实提取引擎接上之后会更明显：单张图十几秒，页面加载本来就慢，再没有加载态就分不清"在跑"和"挂了"（这和票 26 是同一类问题的两个面）。

## 三、122 行手写 CSS

`app/globals.css` 第 31 行之后定义了 10 个手写工具类：`.glass-shell`、`.glass-panel`、`.glass-card`、`.glass-card-subtle`、`.glass-warning-pill`、`.btn-primary-capsule`、`.btn-secondary-capsule`、`.blueprint-grid-bg`、`.nav-item-active`、`.nav-item-inactive`。

这些全都是 Tailwind 能表达的东西（半透明背景 + backdrop-blur + 多层 shadow + 圆角 + hover/active 变换）。项目规范是"优先使用 Tailwind CSS，避免自定义 CSS"。文件前 20 行的 `@theme inline` 令牌定义是正确做法，问题只在 31 行之后——可以收敛成 Tailwind v4 的 `@utility`，或直接在组件里用类名组合。

顺带：`package.json` 声明了 `lucide-react`，但全仓库除了 lockfile 没有任何引用（项目用的是自己手写的 `components/Icons.tsx`）。纯包体积负担，删掉。

**Blocked by:** 20（lint error 的来源就是那段要删的定价逻辑，先删再修剩下的）

**Status:** claimed

- [ ] `pnpm lint` 零 error 零 warning
- [ ] `AppHeader` 的 `backLabel` 真正用上，返回链接有可访问名称而不只是 `←`
- [ ] 有 `global-error.tsx` 兜底，用户能看到"服务暂时不可用"级别的说明与重试入口
- [ ] 后端不可用时不再出现 Next.js 默认错误页
- [ ] 主要页面（**零件图**列表与详情、**报价任务**列表与详情、管理员各页）有 `loading.tsx`
- [ ] `globals.css` 第 31 行之后的手写工具类收敛掉，样式改用 Tailwind 表达
- [ ] 移除未使用的 `lucide-react` 依赖
- [ ] CI 的 frontend job 在 main 上转绿

## Comments
