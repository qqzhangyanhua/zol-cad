import Link from "next/link";

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
        <nav className="mt-1 flex items-center gap-3 text-xs text-stone-500">
          <Link href="/part-drawings" className="hover:text-stone-800">
            零件图
          </Link>
          <Link href="/quote-tasks" className="hover:text-stone-800">
            报价任务
          </Link>
          {user.role === "admin" ? (
            <>
              <Link href="/admin/accounts" className="hover:text-stone-800">
                账号
              </Link>
              <Link href="/admin/processing-records" className="hover:text-stone-800">
                处理记录
              </Link>
              <Link href="/admin/preferences" className="hover:text-stone-800">
                本厂偏好
              </Link>
              <Link href="/processing-time" className="hover:text-stone-800">
                处理耗时
              </Link>
              <Link href="/admin/correction-stats" className="hover:text-stone-800">
                修正记录
              </Link>
              <Link href="/admin/tenant-data" className="hover:text-stone-800">
                本厂数据
              </Link>
            </>
          ) : null}
        </nav>
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
