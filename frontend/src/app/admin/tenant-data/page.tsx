import { redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
import { TenantDataDeletePanel } from "@/components/TenantDataDeletePanel";
import { TenantDataExportPanel } from "@/components/TenantDataExportPanel";
import { fetchBackend } from "@/lib/backend";
import { parseCurrentUser } from "@/lib/types";

export default async function AdminTenantDataPage() {
  const meResponse = await fetchBackend("/auth/me");
  if (meResponse.status === 401) {
    redirect("/login");
  }
  if (!meResponse.ok) {
    throw new Error("无法读取当前用户");
  }
  const user = parseCurrentUser(await meResponse.json());
  if (user.role !== "admin") {
    redirect("/part-drawings");
  }

  return (
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-5 px-6 py-5">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">本厂数据</h1>
          <p className="mt-1 text-sm text-stone-500">
            管理员可以把本厂数据一次性带走，也可以在二次确认后彻底清除。零件图存在第三方云上，这是合作终止时必须答得上的问题。
          </p>
        </div>
        <TenantDataExportPanel />
        <TenantDataDeletePanel factoryName={user.factory_name} />
      </main>
    </div>
  );
}
