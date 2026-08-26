import type { ReactNode } from "react";
import { AppSidebar } from "@/components/AppSidebar";
import type { CurrentUser } from "@/lib/types";

type AppShellProps = {
  user: CurrentUser;
  children: ReactNode;
};

export function AppShell({ user, children }: AppShellProps) {
  return (
    <div className="flex h-screen w-full overflow-hidden p-3 md:p-4 gap-3 md:gap-4">
      {/* Left Floating Sidebar */}
      <AppSidebar user={user} />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col min-w-0 overflow-y-auto">
        {children}
      </div>
    </div>
  );
}
