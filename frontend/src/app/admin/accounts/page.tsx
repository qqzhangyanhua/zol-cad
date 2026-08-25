import { redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
import { CreateQuoterForm } from "@/components/CreateQuoterForm";
import { FactoryAccountList } from "@/components/FactoryAccountList";
import { fetchBackend } from "@/lib/backend";
import { parseCurrentUser, parseFactoryAccountList } from "@/lib/types";

export default async function AdminAccountsPage() {
  const [meResponse, listResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend("/admin/accounts"),
  ]);

  if (meResponse.status === 401 || listResponse.status === 401) {
    redirect("/login");
  }
  if (!meResponse.ok) {
    throw new Error("无法读取当前用户");
  }
  const user = parseCurrentUser(await meResponse.json());
  if (user.role !== "admin" || listResponse.status === 403) {
    redirect("/part-drawings");
  }
  if (!listResponse.ok) {
    throw new Error("无法读取本厂账号");
  }
  const accounts = parseFactoryAccountList(await listResponse.json());

  return (
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-5 px-6 py-5">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">账号管理</h1>
          <p className="mt-1 text-sm text-stone-500">为本厂报价员创建或停用账号。权限只有管理员 / 报价员两档。</p>
        </div>
        <CreateQuoterForm />
        <FactoryAccountList items={accounts.items} />
      </main>
    </div>
  );
}
