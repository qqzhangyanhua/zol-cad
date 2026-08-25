import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
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
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-6">
        <div>
          <Link href="/quote-tasks" className="text-xs text-stone-500 hover:text-stone-800">
            ← 返回报价任务
          </Link>
          <h1 className="mt-2 text-xl font-semibold text-stone-900">{task.name}</h1>
          <p className="mt-1 text-sm text-stone-500">
            客户 {task.customer_name} · {task.review_status} · 创建于{" "}
            {new Date(task.created_at).toLocaleString("zh-CN")}
          </p>
        </div>
        <QuoteSheetExportButton task={task} />
        <QuoteTaskDrawingManager
          task={task}
          otherTasks={otherTasks}
          unassignedDrawings={unassignedDrawings}
        />
      </main>
    </div>
  );
}
