import { notFound, redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
import { InFlightRefresh } from "@/components/InFlightRefresh";
import { QuoteSheetExportButton } from "@/components/QuoteSheetExportButton";
import { QuoteTaskDrawingManager } from "@/components/QuoteTaskDrawingManager";
import { fetchBackend } from "@/lib/backend";
import { parseCurrentUser, parsePartDrawingList, parseQuoteTaskDetail, parseQuoteTaskList } from "@/lib/types";

type QuoteTaskDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function QuoteTaskDetailPage({ params }: QuoteTaskDetailPageProps) {
  const { id } = await params;
  const [meResponse, taskResponse, tasksResponse, drawingsResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend(`/quote-tasks/${id}`),
    fetchBackend("/quote-tasks"),
    fetchBackend("/part-drawings"),
  ]);

  if (
    meResponse.status === 401 ||
    taskResponse.status === 401 ||
    tasksResponse.status === 401 ||
    drawingsResponse.status === 401
  ) {
    redirect("/login");
  }
  if (taskResponse.status === 404) {
    notFound();
  }
  if (!meResponse.ok || !taskResponse.ok || !tasksResponse.ok || !drawingsResponse.ok) {
    throw new Error("无法读取报价任务");
  }

  const user = parseCurrentUser(await meResponse.json());
  const task = parseQuoteTaskDetail(await taskResponse.json());
  const tasks = parseQuoteTaskList(await tasksResponse.json());
  const drawings = parsePartDrawingList(await drawingsResponse.json());
  const otherTasks = tasks.items.filter((item) => item.id !== task.id);
  const unassignedDrawings = drawings.items.filter((item) => item.quote_task_id === null);

  return (
    <AppShell user={user}>
      <AppHeader
        projectCode={task.name}
        title={task.name}
        backHref="/quote-tasks"
        backLabel="返回任务列表"
        subtitle={`客户: ${task.customer_name} · 状态: ${task.review_status} · 创建于 ${new Date(
          task.created_at,
        ).toLocaleString("zh-CN")}`}
      />
      <main className="flex flex-1 flex-col gap-4 pb-6">
        <InFlightRefresh statuses={task.drawings.map((drawing) => drawing.status)} />
        <QuoteSheetExportButton task={task} />
        <QuoteTaskDrawingManager
          task={task}
          otherTasks={otherTasks}
          unassignedDrawings={unassignedDrawings}
        />
      </main>
    </AppShell>
  );
}
