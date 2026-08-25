import { redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
import { EmptyPartDrawingState } from "@/components/EmptyPartDrawingState";
import { PartDrawingList } from "@/components/PartDrawingList";
import { fetchBackend } from "@/lib/backend";
import { parseCurrentUser, parsePartDrawingList } from "@/lib/types";

export default async function PartDrawingsPage() {
  const [meResponse, listResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend("/part-drawings"),
  ]);

  if (meResponse.status === 401 || listResponse.status === 401) {
    redirect("/login");
  }
  if (!meResponse.ok || !listResponse.ok) {
    throw new Error("无法读取零件图列表");
  }

  const user = parseCurrentUser(await meResponse.json());
  const list = parsePartDrawingList(await listResponse.json());

  return (
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="flex flex-1 flex-col">
        <div className="px-6 py-5">
          <h1 className="text-xl font-semibold text-stone-900">零件图</h1>
          <p className="mt-1 text-sm text-stone-500">本厂已上传的零件图</p>
        </div>
        {list.items.length === 0 ? (
          <EmptyPartDrawingState />
        ) : (
          <PartDrawingList items={list.items} />
        )}
      </main>
    </div>
  );
}
