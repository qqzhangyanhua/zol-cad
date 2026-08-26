"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { AppSidebar } from "@/components/AppSidebar";
import { SidebarNavContext } from "@/components/SidebarNavContext";
import type { CurrentUser } from "@/lib/types";

type AppShellProps = {
  user: CurrentUser;
  children: ReactNode;
};

export function AppShell({ user, children }: AppShellProps) {
  const [open, setOpen] = useState(false);
  const openSidebar = useCallback(() => {
    setOpen(true);
  }, []);
  const closeSidebar = useCallback(() => {
    setOpen(false);
  }, []);
  const nav = useMemo(
    () => ({ open, openSidebar, closeSidebar }),
    [open, openSidebar, closeSidebar],
  );

  useEffect(() => {
    if (!open) {
      return;
    }
    function onKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        closeSidebar();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, closeSidebar]);

  return (
    <SidebarNavContext.Provider value={nav}>
      <div className="flex h-screen w-full overflow-hidden p-3 md:p-4 md:gap-4">
        {open ? (
          <button
            type="button"
            className="fixed inset-0 z-40 bg-slate-900/40 md:hidden"
            aria-label="关闭导航"
            onClick={closeSidebar}
          />
        ) : null}
        <AppSidebar user={user} />
        <div className="flex min-w-0 flex-1 flex-col overflow-y-auto">{children}</div>
      </div>
    </SidebarNavContext.Provider>
  );
}
