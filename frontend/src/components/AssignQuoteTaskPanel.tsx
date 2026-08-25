"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { QuoteTaskSummary } from "@/lib/types";
import { parseQuoteTaskDetail, readErrorDetail } from "@/lib/types";

type AssignQuoteTaskPanelProps = {
  drawingId: string;
  currentTaskId: string | null;
  tasks: QuoteTaskSummary[];
};

export function AssignQuoteTaskPanel({ drawingId, currentTaskId, tasks }: AssignQuoteTaskPanelProps) {
  const router = useRouter();
  const [taskId, setTaskId] = useState(currentTaskId ?? "");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const currentTask = tasks.find((item) => item.id === currentTaskId) ?? null;

  async function assignTo(nextTaskId: string): Promise<void> {
    setPending(true);
    setError(null);
    const response = await fetch(`/api/quote-tasks/${nextTaskId}/part-drawings`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ part_drawing_id: drawingId }),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "归集失败");
      setPending(false);
      return;
    }
    parseQuoteTaskDetail(payload);
    setPending(false);
    router.refresh();
  }

  async function removeFromCurrent(): Promise<void> {
    if (!currentTaskId) {
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch(`/api/quote-tasks/${currentTaskId}/part-drawings/${drawingId}`, {
      method: "DELETE",
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "移出失败");
      setPending(false);
      return;
    }
    parseQuoteTaskDetail(payload);
    setTaskId("");
    setPending(false);
    router.refresh();
  }

  return (
    <section className="border-b border-stone-200 bg-white px-6 py-4">
      <h2 className="text-sm font-semibold text-stone-900">报价任务</h2>
      <p className="mt-1 text-xs text-stone-500">
        {currentTask
          ? `当前归入「${currentTask.name}」（客户 ${currentTask.customer_name}）。一张零件图同时最多属于一个报价任务。`
          : "这张零件图尚未归入任何报价任务，也可以继续单独处理。"}
      </p>
      {tasks.length === 0 ? (
        <p className="mt-3 text-xs text-stone-500">
          还没有报价任务。请先到历史记录页创建一个。
        </p>
      ) : (
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <label className="flex min-w-56 flex-1 flex-col gap-2 text-sm font-medium text-stone-800">
            归入或移到
            <select
              value={taskId}
              onChange={(event) => setTaskId(event.target.value)}
              className="h-10 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm font-normal"
            >
              <option value="">不归入报价任务</option>
              {tasks.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} · {item.customer_name}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            disabled={pending || taskId === "" || taskId === currentTaskId}
            onClick={() => {
              void assignTo(taskId);
            }}
            className="h-10 rounded-lg bg-stone-900 px-4 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-60"
          >
            {currentTaskId ? "移到所选任务" : "归入所选任务"}
          </button>
          {currentTaskId ? (
            <button
              type="button"
              disabled={pending}
              onClick={() => {
                void removeFromCurrent();
              }}
              className="h-10 rounded-lg px-3 text-sm text-stone-600 hover:bg-stone-100 disabled:opacity-60"
            >
              移出任务
            </button>
          ) : null}
        </div>
      )}
      {error ? (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
