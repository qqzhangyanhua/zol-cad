import { redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
import { EmptyPartDrawingState } from "@/components/EmptyPartDrawingState";
import { PartDrawingList } from "@/components/PartDrawingList";
import { PartDrawingUploadPanel } from "@/components/PartDrawingUploadPanel";
import { QualityGradeDisclaimer } from "@/components/QualityGradeDisclaimer";
import { fetchBackend } from "@/lib/backend";
import { parseCurrentUser, parsePartDrawingList, parseQuoteTaskList } from "@/lib/types";

export default async function PartDrawingsPage() {
  const [meResponse, listResponse, tasksResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend("/part-drawings"),
    fetchBackend("/quote-tasks"),
  ]);

  if (meResponse.status === 401 || listResponse.status === 401 || tasksResponse.status === 401) {
    redirect("/login");
  }
  if (!meResponse.ok || !listResponse.ok || !tasksResponse.ok) {
    throw new Error("无法读取零件图列表");
  }

  const user = parseCurrentUser(await meResponse.json());
  const list = parsePartDrawingList(await listResponse.json());
  const tasks = parseQuoteTaskList(await tasksResponse.json());
  const quoteTaskNames = Object.fromEntries(tasks.items.map((item) => [item.id, item.name]));

  return (
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="flex flex-1 flex-col">
        <div className="px-6 py-5">
          <h1 className="text-xl font-semibold text-stone-900">零件图</h1>
          <p className="mt-1 text-sm text-stone-500">
            {user.role === "admin" ? "本厂全部零件图" : "你自己处理过的零件图"}
          </p>
          <div className="mt-2">
            <QualityGradeDisclaimer
              text={
                list.items[0]?.quality_grade_disclaimer ??
                "图纸质量分级只表示图纸本身的质量，不代表结果可以免核。"
              }
            />
          </div>
        </div>
        <PartDrawingUploadPanel />
        {list.items.length === 0 ? (
          <EmptyPartDrawingState />
        ) : (
          <PartDrawingList items={list.items} quoteTaskNames={quoteTaskNames} />
        )}
      </main>
    </div>
  );
}
