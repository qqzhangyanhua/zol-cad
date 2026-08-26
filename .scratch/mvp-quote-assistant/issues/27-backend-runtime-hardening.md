# 27 — 后端运行时加固与部署产物

**What to build:** 后端的领域逻辑与测试都很扎实，但它现在没法安全地部署出去。这张票收的是一组"跑起来才会咬人"的缺口——它们都在缝 1 的观测范围之外，因为缝 1 用 ASGI 测试客户端直接打进应用，从不经过真实进程边界。

## 启动时的滞留回收在多进程下会互相打断

`lifespan` 里无条件执行 `_recover_stranded_part_drawings(session_factory)`，回收范围是「已上传 / 分级中 / 提取中」，全部改成**提取失败**。`RecoverStrandedPartDrawings` 的注释写的是"进程重启后这三态都不可能还有人在跑"——**这个前提只在单进程下成立**。

`uvicorn --workers N`、滚动发布、或任何第二个实例启动，都会把另一个进程正在处理的**零件图**改成失败；而那个进程手里持的是 stale 的 `PartDrawing`，随后 `drawings.save()` 又会把状态覆盖回去。两个进程互相踩，最终状态取决于时序。

这不是"以后再说"的问题：任何真实部署都会有滚动发布。要么用锁 / 租约 / 单例标记让回收只发生一次且只回收真正无主的作业，要么明确把部署形态钉死在单进程并在 README 与部署产物里写清楚（MVP 的负载是一家工厂几个报价员，单进程完全够——但这必须是一个写下来的决定，不能是一句注释里的隐含假设）。

顺带 `_recover_stranded_part_drawings` 没有 try/except，扫描一抛异常整个应用起不来。

## 没有行级锁，重试与后台作业会双跑

`repositories.py` 全库没有 `with_for_update`。后果有两个：

- 后台作业正在跑时，**报价员**点"重试"可能读到同一状态并双双推进——真实模型上就是两次付费调用，加上事件序号错乱。
- `PartDrawingEventRepository.next_sequence` 是"读-算-写"，并发下会产生重复 `sequence_no`。而**处理耗时**依赖事件序列的完整性（ADR-0006 把"每次处理必须留关键时间戳"列为硬需求）。

## 生产默认值不安全，且启动不校验

- `object_sign_secret` 默认 `"dev-object-sign-secret"`。本地存储的签名 URL 用它做 HMAC——忘了改就等于签名形同虚设。
- `demo_password_a` / `demo_password_b` 默认 `"change-me-a"` / `"change-me-b"`。
- session cookie 缺 `secure=True`，明文 HTTP 也会发送。**零件图**是客户的保密资产（用户故事 55、61），会话被截等于整个租户边界失效。

需要一个启动时的配置校验：非本地环境下这些占位值必须被覆盖，否则拒绝启动。**失败要发生在启动时，不能是某个用户某天发现签名能伪造。**

## 生产默认的作业实现零测试覆盖

`part_drawing_processor` 生产默认 `thread`，但 `conftest.py` 把所有缝 1 测试固定成 `inline`，异步测试用的是 `DeferredPartDrawingProcessor`。`ThreadPartDrawingProcessor`——也就是真正会在生产跑的那个——没有一条测试打进去。

顺带 `build_part_drawing_processor` 对未知值静默回落 `thread`，而 `normalize_extraction_engine` 对未知值抛错。两处行为不一致，应该统一成抛错。

## 上传先全量读进内存再校验大小

路由里 `await upload.read()` 拿到完整字节，之后才在领域层比对 20MB 上限。一次批量传 10 个 500MB 文件可以直接打爆内存——而批量上传是产品明确支持的场景（用户故事 2）。应当边读边计数，超限即中断。

## 没有全局异常处理器，也没有日志配置

- `app.py` 没有 `add_exception_handler`。未被路由显式 catch 的 `DomainError` 会变成 500 + traceback 直接吐给客户端。
- 全库没有 `basicConfig` / `dictConfig`。`vendor.py` 与 `background.py` 的 `LOGGER` 在默认 root 配置下 INFO 级不输出——**后台作业失败会完全静默**。真实引擎接上之后，这是唯一能看到"模型返回了什么、为什么校验失败"的地方（票 21 依赖它）。

## 其他

- `/health` 只返回 `{"status": "ok"}`，不检查数据库。负载均衡器会把一个连不上库的实例判为健康。
- 没有 Dockerfile 或任何部署产物；`dev.sh` 用的是 `uvicorn --reload` 单进程开发模式。
- 保密说明页依赖运行时能在磁盘找到仓库文件：`find_repo_file` 向上遍历找 `docs/adr/0009-*.md`。任何只打包 `backend/` 的部署会 `FileNotFoundError` → `/admin/confidentiality` 500。这块内容应当随代码打包，或落成数据。
- 提取的超时 / 重试 / 并发上限不可配置（`config.py` 里没有对应字段，`vendor.py` 里只有硬编码文案）。作业并发度固定 4，队列无上界无背压——批量 50 张时全部排在一个无界队列里。
- `InMemoryExtractionCostCounter` 不持久化、无查询接口、`events` 列表无上界、进程重启即清零，且 `estimated_cost` 永远是 `None`。票 17 的验收项"单张调用成本可观测"实际不成立。这条可以拆出去单独做，但至少要给 `events` 加上界，避免长跑进程内存泄漏。
- 没有请求体大小限制中间件、没有速率限制。

**Status:** claimed

- [ ] 部署形态被明确决定并写下来（单进程 / 多进程），滞留回收的正确性与该决定一致
- [ ] 回收逻辑不会打断另一个活着的进程正在处理的作业
- [ ] 回收失败不阻止应用启动
- [ ] 同一张**零件图**不会被后台作业与重试同时推进；事件 `sequence_no` 在并发下不重复
- [ ] 启动时校验配置：非本地环境下签名密钥与 demo 密码必须被覆盖，否则拒绝启动
- [ ] session cookie 带 `secure`（本地开发可通过配置放开）
- [ ] 生产默认的作业实现有测试覆盖
- [ ] `part_drawing_processor` 未知值抛错，与引擎选择的行为一致
- [ ] 上传超限在读完整个文件之前中断
- [ ] 有全局异常处理器，领域错误不再漏成 500 + traceback
- [ ] 有日志配置，后台作业失败可见
- [ ] `/health` 检查数据库连通性
- [ ] 有 Dockerfile / 部署产物，不依赖 `--reload`
- [ ] 保密说明内容不依赖运行时能找到仓库源文件
- [ ] 提取超时、重试次数、作业并发度可配置；作业队列有上界
- [ ] `InMemoryExtractionCostCounter` 的 `events` 有上界

## Comments
