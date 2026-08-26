import { redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
import { EmptyPartDrawingState } from "@/components/EmptyPartDrawingState";
import { InFlightRefresh } from "@/components/InFlightRefresh";
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
    <AppShell user={user}>
      <AppHeader
        title="零件图分析与评审"
        subtitle={user.role === "admin" ? "本厂全部图纸，支持智能读图与特征提取" : "处理过的图纸与提取结果"}
      />
      <main className="flex flex-1 flex-col pb-6">
        <div className="mb-3">
          <QualityGradeDisclaimer
            text={
              list.items[0]?.quality_grade_disclaimer ??
              "图纸质量分级只表示图纸本身的质量，不代表结果可以免核。"
            }
          />
        </div>
        <PartDrawingUploadPanel />
        <InFlightRefresh statuses={list.items.map((item) => item.status)} />
        {list.items.length === 0 ? (
          <EmptyPartDrawingState />
        ) : (
          <PartDrawingList items={list.items} quoteTaskNames={quoteTaskNames} />
        )}
      </main>
    </AppShell>
  );
}
