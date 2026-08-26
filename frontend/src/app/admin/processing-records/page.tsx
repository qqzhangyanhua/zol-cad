import { redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
import { FactoryProcessingRecordTable } from "@/components/FactoryProcessingRecordTable";
import { fetchBackend } from "@/lib/backend";
import { parseCurrentUser, parseFactoryProcessingRecordList } from "@/lib/types";

export default async function AdminProcessingRecordsPage() {
  const [meResponse, listResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend("/admin/processing-records"),
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
    throw new Error("无法读取全厂处理记录");
  }
  const records = parseFactoryProcessingRecordList(await listResponse.json());

  return (
    <AppShell user={user}>
      <AppHeader
        title="全厂图纸处理记录"
        subtitle="审计与追踪本厂所有报价员的图纸解析与复核记录"
      />
      <main className="flex flex-1 flex-col pb-6">
        <div className="glass-card p-5 backdrop-blur-xl">
          <FactoryProcessingRecordTable items={records.items} />
        </div>
      </main>
    </AppShell>
  );
}
