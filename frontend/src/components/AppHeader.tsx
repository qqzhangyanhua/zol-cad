import type { ReactNode } from "react";
import Link from "next/link";

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
  backLabel = "返回",
}: AppHeaderProps) {
  return (
    <header className="glass-card mb-3 flex flex-wrap items-center justify-between gap-4 px-6 py-3.5 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        {backHref ? (
          <Link
            href={backHref}
            aria-label={backLabel}
            className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/70 text-slate-600 transition hover:bg-white hover:text-slate-900"
          >
            <span aria-hidden="true">←</span>
            <span className="sr-only">{backLabel}</span>
          </Link>
        ) : null}

        <div>
          <div className="flex items-center gap-2">
            {projectCode ? (
              <div className="inline-flex items-center gap-1.5 rounded-full border border-white/90 bg-white/80 px-3 py-1 text-xs font-semibold text-slate-800 shadow-xs">
                <span className="font-normal text-slate-400">项目 /</span>
                <span>{projectCode}</span>
              </div>
            ) : null}
            {title ? (
              <h1 className="text-base font-bold tracking-tight text-slate-900">{title}</h1>
            ) : null}
          </div>
          {subtitle ? <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p> : null}
        </div>
      </div>

      {actions ? <div className="flex items-center gap-2.5">{actions}</div> : null}
    </header>
  );
}
