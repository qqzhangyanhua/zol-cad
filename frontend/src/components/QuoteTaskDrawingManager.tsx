"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type { PartDrawing, QuoteTaskDetail, QuoteTaskSummary } from "@/lib/types";
import { parseQuoteTaskDetail, readErrorDetail } from "@/lib/types";

type QuoteTaskDrawingManagerProps = {
  task: QuoteTaskDetail;
  otherTasks: QuoteTaskSummary[];
  unassignedDrawings: PartDrawing[];
};

export function QuoteTaskDrawingManager({
  task,
  otherTasks,
  unassignedDrawings,
}: QuoteTaskDrawingManagerProps) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [selectedDrawingId, setSelectedDrawingId] = useState(unassignedDrawings[0]?.id ?? "");
  const availableIds = unassignedDrawings.map((drawing) => drawing.id);
  const effectiveSelectedId = availableIds.includes(selectedDrawingId)
    ? selectedDrawingId
    : (availableIds[0] ?? "");

  async function assign(drawingId: string, taskId: string): Promise<void> {
    setPendingId(drawingId);
    setError(null);
    const response = await fetch(`/api/quote-tasks/${taskId}/part-drawings`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ part_drawing_id: drawingId }),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "归集零件图失败");
      setPendingId(null);
      return;
    }
    parseQuoteTaskDetail(payload);
    setPendingId(null);
    router.refresh();
  }

  async function remove(drawingId: string): Promise<void> {
    setPendingId(drawingId);
    setError(null);
    const response = await fetch(`/api/quote-tasks/${task.id}/part-drawings/${drawingId}`, {
      method: "DELETE",
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "移出零件图失败");
      setPendingId(null);
      return;
    }
    parseQuoteTaskDetail(payload);
    setPendingId(null);
    router.refresh();
  }

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-sm font-semibold text-stone-900">任务内零件图</h2>
        <p className="mt-1 text-xs text-stone-500">
          每张零件图显示各自的复核状态。归错了可以移出，或移到另一个报价任务。
        </p>
      </div>
      {task.drawings.length === 0 ? (
        <p className="rounded-xl border border-dashed border-stone-200 bg-white px-4 py-8 text-center text-sm text-stone-500">
          这个报价任务还没有零件图。
        </p>
      ) : (
        <ul className="divide-y divide-stone-200 overflow-hidden rounded-xl border border-stone-200 bg-white">
          {task.drawings.map((drawing) => (
            <li key={drawing.id} className="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <Link href={`/part-drawings/${drawing.id}`} className="block truncate text-sm font-medium text-stone-900 hover:underline">
                  {drawing.original_filename}
                </Link>
                <p className="mt-1 text-xs text-stone-500">复核状态：{drawing.status}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {otherTasks.length > 0 ? (
                  <label className="flex items-center gap-2 text-xs text-stone-600">
                    移到
                    <select
                      disabled={pendingId === drawing.id}
                      defaultValue=""
                      onChange={(event) => {
                        const nextTaskId = event.target.value;
                        if (nextTaskId) {
                          void assign(drawing.id, nextTaskId);
                          event.target.value = "";
                        }
                      }}
                      className="h-9 rounded-lg border border-stone-200 bg-stone-50 px-2"
                    >
                      <option value="">选择任务</option>
                      {otherTasks.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : null}
                <button
                  type="button"
                  disabled={pendingId === drawing.id}
                  onClick={() => {
                    void remove(drawing.id);
                  }}
                  className="h-9 rounded-lg px-3 text-xs text-stone-600 hover:bg-stone-100 disabled:opacity-60"
                >
                  移出任务
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {unassignedDrawings.length > 0 ? (
        <form
          className="flex flex-wrap items-end gap-3 rounded-xl border border-stone-200 bg-white p-4"
          onSubmit={(event) => {
            event.preventDefault();
            if (effectiveSelectedId) {
              void assign(effectiveSelectedId, task.id);
            }
          }}
        >
          <label className="flex min-w-56 flex-1 flex-col gap-2 text-sm font-medium text-stone-800">
            归入未归集的零件图
            <select
              value={effectiveSelectedId}
              onChange={(event) => setSelectedDrawingId(event.target.value)}
              className="h-10 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm font-normal"
            >
              {unassignedDrawings.map((drawing) => (
                <option key={drawing.id} value={drawing.id}>
                  {drawing.original_filename}
                </option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            disabled={pendingId !== null || effectiveSelectedId === ""}
            className="h-10 rounded-lg bg-stone-900 px-4 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-60"
          >
            归入此任务
          </button>
        </form>
      ) : (
        <p className="text-xs text-stone-500">本厂目前没有未归集的零件图。</p>
      )}

      {error ? (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
