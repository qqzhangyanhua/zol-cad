import type { ReactNode } from "react";
import Link from "next/link";
import { ExportIcon, SaveDraftIcon, SubmitIcon } from "@/components/Icons";

type AppHeaderProps = {
  title?: string;
  projectCode?: string;
  subtitle?: string;
  actions?: ReactNode;
  backHref?: string;
  backLabel?: string;
};

export function AppHeader({
  title,
  projectCode,
  subtitle,
  actions,
  backHref,
  backLabel,
}: AppHeaderProps) {
  return (
    <header className="glass-card mb-3 flex flex-wrap items-center justify-between gap-4 px-6 py-3.5 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        {backHref ? (
          <Link
            href={backHref}
            className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/70 text-slate-600 transition hover:bg-white hover:text-slate-900"
          >
            ←
          </Link>
        ) : null}

        <div>
          <div className="flex items-center gap-2">
            {projectCode ? (
              <div className="inline-flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-slate-800 shadow-xs border border-white/90">
                <span className="text-slate-400 font-normal">项目 /</span>
                <span>{projectCode}</span>
                <span className="text-slate-400 text-[10px]">▼</span>
              </div>
            ) : null}
            {title ? (
              <h1 className="text-base font-bold text-slate-900 tracking-tight">{title}</h1>
            ) : null}
          </div>
          {subtitle ? (
            <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>
          ) : null}
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        {actions ? (
          actions
        ) : (
          <>
            <button
              type="button"
              className="btn-secondary-capsule gap-1.5 px-3.5 py-1.5 text-xs text-slate-700 font-medium cursor-pointer"
            >
              <SaveDraftIcon className="h-3.5 w-3.5 text-slate-500" />
              保存草稿
            </button>
            <button
              type="button"
              className="btn-secondary-capsule gap-1.5 px-3.5 py-1.5 text-xs text-slate-700 font-medium cursor-pointer"
            >
              <ExportIcon className="h-3.5 w-3.5 text-slate-500" />
              导出报告
            </button>
            <button
              type="button"
              className="btn-primary-capsule gap-1.5 px-4 py-1.5 text-xs text-white font-medium cursor-pointer"
            >
              <SubmitIcon className="h-3.5 w-3.5" />
              提交报价
            </button>
          </>
        )}
      </div>
    </header>
  );
}
