import { redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
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
    <AppShell user={user}>
      <AppHeader
        title="本厂数据资产与导出"
        subtitle="支持本厂所有图纸与提取记录的一次性备份导出及合规销毁"
      />
      <main className="flex flex-1 flex-col gap-5 pb-6">
        <div className="glass-card p-5 backdrop-blur-xl">
          <TenantDataExportPanel />
        </div>
        <div className="glass-card p-5 backdrop-blur-xl">
          <TenantDataDeletePanel factoryName={user.factory_name} />
        </div>
      </main>
    </AppShell>
  );
}
