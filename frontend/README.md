# 机加工报价辅助 — 前端

Next.js + TypeScript + Tailwind。依赖用 `pnpm` 管理。服务端只做 BFF 代理，不包含领域判断。

```bash
cd frontend
pnpm install
# BACKEND_URL 指向后端，默认 http://127.0.0.1:8000
pnpm dev
```

打开 http://127.0.0.1:3000 ，未登录会进入登录页。
