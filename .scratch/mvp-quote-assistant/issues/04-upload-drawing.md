# 04 — 上传零件图并查看原图

**What to build:** **报价员**把一张或多张**零件图**（PDF 或图片）拖进上传区，上传完成后它们出现在列表里；点开任意一张能看到原图，并能自由缩放平移看清扫描件上的小字。

这一票引入对象存储的窄接口与阿里云 OSS 实现。用例层只依赖这个窄接口（存、取、签发临时访问 URL、删），不直接引用 OSS SDK——ADR-0005 把私有化部署列为后续选项，届时存储后端必然要换。

**Blocked by:** 03

**Status:** claimed

- [x] **报价员**能拖拽或选择上传单张**零件图**，格式支持 PDF 与常见图片
- [x] 能一次选中多张批量上传，对应客户一次发来一整包图的真实场景
- [x] 超出单文件大小上限或 PDF 页数上限时被拒绝，提示写明具体原因与限制数值
- [x] 多页 PDF 上传时明确告知只处理指定的那一页，默认第 1 页，且报价员能改
- [x] 上传后的**零件图**出现在列表中，能看到文件名与上传时间
- [x] 点开能查看原图，支持缩放与平移
- [x] 原图通过后端签发的短时效临时 URL 访问，OSS Bucket 不允许公共读，开启服务端加密
- [x] 用例层只依赖对象存储窄接口；测试中该接口指向本地临时目录
- [x] **报价员**只能看到本厂的**零件图**

## Comments

实现已落在 PR：https://github.com/qqzhangyanhua/zol-cad/pull/4

设计要点：

- 上传限制写在领域层：单文件 20 MB、PDF 20 页。拒绝文案同时写出原因与数值。
- 多页 PDF 默认 `selected_page=1`，上传区可改；后端再校验页码范围。
- `ObjectStorage` 窄接口（store / fetch / sign_access_url / delete）。用例层禁止引用 `oss2`。测试与本地开发用 `LocalDirectoryObjectStorage` 指向临时目录；生产用 `OssObjectStorage`（put 时 `x-oss-server-side-encryption: AES256` + private ACL）。
- 原图 `GET /part-drawings/{id}/original` 返回短时效签名 URL。本地实现走 `/object-store/...` HMAC 签名；OSS 走 Bucket 预签名。
- 租户边界仍是工厂。`UploadPartDrawings` / `GetPartDrawing` / `IssueOriginalAccessUrl` 的 `execute()` 都不接受 `factory_id`。甲厂报价员列表为空、详情与原图 URL 均 404。
- 缝 1：26 passed。CI seam-1 backend + frontend 已绿。本环境无 Docker，用本机 Postgres + `QA_TEST_DATABASE_URL`。

浏览器已走通：登录 → 空列表上传区 → 批量上传 PDF+PNG 出现在列表（文件名与时间）→ 打开原图缩放平移 → 多页 PDF 改到第 2 页 → 21 页 PDF 与 txt 被拒绝并写明原因。
