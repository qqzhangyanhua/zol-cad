"use client";

import Link from "next/link";

type ServiceUnavailableProps = {
  error?: Error & { digest?: string };
  onRetry: () => void;
};

function detailMessage(error: Error | undefined): string {
  if (error !== undefined && /[\u4e00-\u9fff]/.test(error.message)) {
    return error.message;
  }
  return "后端暂时无法响应。请稍后重试。";
}

export function ServiceUnavailable({ error, onRetry }: ServiceUnavailableProps) {
  return (
    <main className="flex min-h-screen flex-1 flex-col items-center justify-center p-6">
      <section className="glass-card w-full max-w-md p-8 text-center backdrop-blur-xl">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">机加工报价辅助</p>
        <h1 className="mt-3 text-lg font-semibold text-slate-900">服务暂时不可用</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">{detailMessage(error)}</p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            onClick={onRetry}
            className="btn-primary-capsule h-9 px-5 text-sm text-white"
          >
            重试
          </button>
          <Link href="/part-drawings" className="btn-secondary-capsule h-9 px-5 text-sm text-slate-700">
            返回零件图列表
          </Link>
        </div>
      </section>
    </main>
  );
}
