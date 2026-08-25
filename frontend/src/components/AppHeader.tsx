import { LogoutButton } from "@/components/LogoutButton";
import type { CurrentUser } from "@/lib/types";

type AppHeaderProps = {
  user: CurrentUser;
};

export function AppHeader({ user }: AppHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-stone-200 bg-white px-6 py-4">
      <div>
        <p className="text-sm font-semibold text-stone-900">机加工报价辅助</p>
        <p className="text-xs text-stone-500">零件图</p>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right text-sm">
          <p className="font-medium text-stone-800">{user.factory_name}</p>
          <p className="text-stone-500">{user.username}</p>
        </div>
        <LogoutButton />
      </div>
    </header>
  );
}
