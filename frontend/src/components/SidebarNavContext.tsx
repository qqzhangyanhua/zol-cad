"use client";

import { createContext, useContext } from "react";

export const APP_SIDEBAR_ID = "app-sidebar";

export type SidebarNavContextValue = {
  open: boolean;
  openSidebar: () => void;
  closeSidebar: () => void;
};

export const SidebarNavContext = createContext<SidebarNavContextValue | null>(null);

export function useSidebarNav(): SidebarNavContextValue {
  const value = useContext(SidebarNavContext);
  if (value === null) {
    throw new Error("useSidebarNav 必须在 AppShell 内使用");
  }
  return value;
}
