import { redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
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
    <AppShell user={user}>
      <AppHeader
        title="账号与组织权限管理"
        subtitle="为本厂工程师分配系统账号与操作权限"
      />
      <main className="flex flex-1 flex-col gap-5 pb-6">
        <div className="glass-card p-5 backdrop-blur-xl">
          <CreateQuoterForm />
        </div>
        <div className="glass-card p-5 backdrop-blur-xl">
          <FactoryAccountList items={accounts.items} />
        </div>
      </main>
    </AppShell>
  );
}
