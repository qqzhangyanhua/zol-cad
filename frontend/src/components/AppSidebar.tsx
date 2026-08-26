"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  CalendarIcon,
  DrawingAnalysisIcon,
  HistoryQuoteIcon,
  KnowledgeIcon,
  LogoIcon,
  ProjectManageIcon,
  QuoteCalcIcon,
  RiskAssessIcon,
  SettingsIcon,
  ShieldCheckIcon,
} from "@/components/Icons";
import { LogoutButton } from "@/components/LogoutButton";
import type { CurrentUser } from "@/lib/types";

type SidebarIcon = typeof DrawingAnalysisIcon;

type SidebarItem = {
  label: string;
  href: string;
  icon: SidebarIcon;
  match: (path: string) => boolean;
};

type AppSidebarProps = {
  user: CurrentUser;
};

export function AppSidebar({ user }: AppSidebarProps) {
  const pathname = usePathname();

  const navItems: SidebarItem[] = [
    {
      label: "零件图",
      href: "/part-drawings",
      icon: DrawingAnalysisIcon,
      match: (path: string) => path.startsWith("/part-drawings"),
    },
    {
      label: "报价任务",
      href: "/quote-tasks",
      icon: ProjectManageIcon,
      match: (path: string) => path.startsWith("/quote-tasks"),
    },
    {
      label: "处理耗时",
      href: "/processing-time",
      icon: QuoteCalcIcon,
      match: (path: string) => path.startsWith("/processing-time"),
    },
    ...(user.role === "admin"
      ? [
          {
            label: "本厂偏好",
            href: "/admin/preferences",
            icon: RiskAssessIcon,
            match: (path: string) => path.startsWith("/admin/preferences"),
          },
          {
            label: "修正统计",
            href: "/admin/correction-stats",
            icon: HistoryQuoteIcon,
            match: (path: string) => path.startsWith("/admin/correction-stats"),
          },
          {
            label: "本厂数据",
            href: "/admin/tenant-data",
            icon: KnowledgeIcon,
            match: (path: string) => path.startsWith("/admin/tenant-data"),
          },
          {
            label: "全厂处理记录",
            href: "/admin/processing-records",
            icon: CalendarIcon,
            match: (path: string) => path.startsWith("/admin/processing-records"),
          },
          {
            label: "保密说明",
            href: "/admin/confidentiality",
            icon: ShieldCheckIcon,
            match: (path: string) => path.startsWith("/admin/confidentiality"),
          },
          {
            label: "系统设置",
            href: "/admin/accounts",
            icon: SettingsIcon,
            match: (path: string) => path.startsWith("/admin/accounts"),
          },
        ]
      : []),
  ];

  return (
    <aside className="glass-panel flex w-64 shrink-0 flex-col justify-between rounded-3xl p-4 shadow-lg backdrop-blur-xl">
      {/* Brand Header */}
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-3 px-2 pt-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600/10 text-blue-600">
            <LogoIcon className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-base font-bold tracking-tight text-slate-900">智造报价助手</h2>
            <p className="text-[11px] font-medium text-slate-400 tracking-wider">CAD Quote Assistant</p>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="flex flex-col gap-1.5">
          {navItems.map((item) => {
            const active = item.match(pathname);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-3 rounded-2xl px-3.5 py-2.5 text-sm transition-all duration-150 ${
                  active ? "nav-item-active" : "nav-item-inactive"
                }`}
              >
                <Icon className={`h-4.5 w-4.5 shrink-0 ${active ? "text-blue-600" : "text-slate-500 group-hover:text-slate-800"}`} />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Area: Organization & User Card */}
      <div className="flex flex-col gap-3 pt-4">
        {/* Org Switcher Card */}
        <div className="glass-card-subtle flex items-center justify-between rounded-2xl p-3 text-xs">
          <div className="min-w-0 flex-1 pr-2">
            <p className="text-[11px] text-slate-400">当前组织</p>
            <p className="truncate font-semibold text-slate-700">{user.factory_name || "精密制造有限公司"}</p>
          </div>
          <span className="text-slate-400">›</span>
        </div>

        {/* User Card */}
        <div className="glass-card-subtle flex items-center justify-between rounded-2xl p-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-tr from-slate-600 to-slate-400 font-semibold text-white text-xs">
              {user.username.slice(0, 2).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-slate-900">{user.username}</p>
              <p className="truncate text-[11px] text-slate-400">
                {user.role === "admin" ? "高级制造工程师 · 管理员" : "报价工程师"}
              </p>
            </div>
          </div>
          <div className="shrink-0 pl-1">
            <LogoutButton />
          </div>
        </div>

        {/* Security / Compliance Badge */}
        <div className="flex items-center justify-between px-2 pt-1 text-[11px] text-slate-400">
          <span>2024 © 智造科技</span>
          <span className="flex items-center gap-1">
            <ShieldCheckIcon className="h-3.5 w-3.5 text-slate-400" />
            数据安全合规
          </span>
        </div>
      </div>
    </aside>
  );
}
