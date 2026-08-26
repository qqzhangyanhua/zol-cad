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
    <section className="space-y-4">
      <div className="glass-card overflow-hidden backdrop-blur-xl">
        <div className="border-b border-slate-100/80 px-6 py-3.5 bg-white/40">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            任务包含零件图 ({task.drawings.length})
          </h2>
        </div>
        {task.drawings.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            当前报价任务还没有归集任何零件图。
          </div>
        ) : (
          <ul className="divide-y divide-slate-100/80">
            {task.drawings.map((drawing) => (
              <li
                key={drawing.id}
                className="flex flex-col gap-3 px-6 py-4 transition hover:bg-white/60 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0 flex-1">
                  <Link
                    href={`/part-drawings/${drawing.id}`}
                    className="block truncate text-sm font-semibold text-slate-900 hover:text-blue-600"
                  >
                    {drawing.original_filename}
                  </Link>
                  <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                    <span className="rounded-md bg-blue-50 px-2 py-0.5 font-medium text-blue-700">
                      {drawing.status}
                    </span>
                    <span>· 点击进入图纸详情与报价评审</span>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2.5 shrink-0">
                  {otherTasks.length > 0 ? (
                    <label className="flex items-center gap-1.5 text-xs text-slate-600">
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
                        className="h-8 rounded-lg border border-slate-200 bg-white/80 px-2 text-xs font-medium"
                      >
                        <option value="">选择其他任务</option>
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
                    className="btn-secondary-capsule h-8 px-3 text-xs text-red-600 hover:text-red-700 cursor-pointer disabled:opacity-60"
                  >
                    移出任务
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {unassignedDrawings.length > 0 ? (
        <form
          className="glass-card p-5 backdrop-blur-xl flex flex-wrap items-end gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            if (effectiveSelectedId) {
              void assign(effectiveSelectedId, task.id);
            }
          }}
        >
          <label className="flex min-w-56 flex-1 flex-col gap-1.5 text-xs font-semibold text-slate-700">
            归入本厂未归集的零件图
            <select
              value={effectiveSelectedId}
              onChange={(event) => setSelectedDrawingId(event.target.value)}
              className="h-9 rounded-xl border border-slate-200 bg-white/80 px-3 text-xs font-medium outline-none"
            >
              {unassignedDrawings.map((drawing) => (
                <option key={drawing.id} value={drawing.id}>
                  {drawing.original_filename} ({drawing.status})
                </option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            disabled={pendingId !== null || effectiveSelectedId === ""}
            className="btn-primary-capsule h-9 px-4 text-xs text-white cursor-pointer disabled:opacity-60"
          >
            + 归入此任务
          </button>
        </form>
      ) : null}

      {error ? (
        <p className="mt-2 text-xs text-red-600 font-medium" role="alert">
          ⚠ {error}
        </p>
      ) : null}
    </section>
  );
}
