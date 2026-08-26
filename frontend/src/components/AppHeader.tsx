"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { MenuIcon } from "@/components/Icons";
import { APP_SIDEBAR_ID, useSidebarNav } from "@/components/SidebarNavContext";

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
  const { open, openSidebar } = useSidebarNav();

  return (
    <header className="glass-card mb-3 flex flex-wrap items-center justify-between gap-3 px-4 py-3 backdrop-blur-xl md:gap-4 md:px-6 md:py-3.5">
      <div className="flex min-w-0 items-center gap-2 md:gap-3">
        <button
          type="button"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/70 text-slate-600 transition hover:bg-white hover:text-slate-900 md:hidden"
          aria-label="打开导航"
          aria-expanded={open}
          aria-controls={APP_SIDEBAR_ID}
          onClick={openSidebar}
        >
          <MenuIcon className="h-4 w-4" aria-hidden="true" />
        </button>
        {backHref ? (
          <Link
            href={backHref}
            aria-label={backLabel}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/70 text-slate-600 transition hover:bg-white hover:text-slate-900"
          >
            <span aria-hidden="true">←</span>
            <span className="sr-only">{backLabel}</span>
          </Link>
        ) : null}

        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            {projectCode ? (
              <div className="inline-flex items-center gap-1.5 rounded-full border border-white/90 bg-white/80 px-3 py-1 text-xs font-semibold text-slate-800 shadow-xs">
                <span className="font-normal text-slate-400">项目 /</span>
                <span className="max-w-[10rem] truncate sm:max-w-none">{projectCode}</span>
              </div>
            ) : null}
            {title ? (
              <h1 className="truncate text-base font-bold tracking-tight text-slate-900">{title}</h1>
            ) : null}
          </div>
          {subtitle ? <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p> : null}
        </div>
      </div>

      {actions ? <div className="flex flex-wrap items-center gap-2.5">{actions}</div> : null}
    </header>
  );
}
