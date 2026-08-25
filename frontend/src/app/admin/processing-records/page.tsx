import { redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
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
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-5 px-6 py-5">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">全厂处理记录</h1>
          <p className="mt-1 text-sm text-stone-500">查看本厂所有报价员处理过的零件图。报价员默认只能看到自己的。</p>
        </div>
        <FactoryProcessingRecordTable items={records.items} />
      </main>
    </div>
  );
}
