"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { parsePartDrawing, readErrorDetail } from "@/lib/types";

type ReviewProgressProps = {
  drawingId: string;
  pendingCount: number;
  pendingLabels: string[];
  reviewed: boolean;
};

export function ReviewProgress({
  drawingId,
  pendingCount,
  pendingLabels,
  reviewed,
}: ReviewProgressProps) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onComplete(): Promise<void> {
    if (pending) {
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch(`/api/part-drawings/${drawingId}/complete-review`, {
      method: "POST",
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "无法标记已复核");
      setPending(false);
      return;
    }
    parsePartDrawing(payload);
    router.refresh();
    setPending(false);
  }

  async function onReopen(): Promise<void> {
    if (pending) {
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch(`/api/part-drawings/${drawingId}/reopen-review`, {
      method: "POST",
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "无法重新打开复核");
      setPending(false);
      return;
    }
    parsePartDrawing(payload);
    router.refresh();
    setPending(false);
  }

  if (reviewed) {
    return (
      <div className="glass-card-subtle rounded-2xl border border-emerald-300/60 bg-emerald-50/70 p-4 shadow-2xs">
        <div className="flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-600 text-[11px] font-bold text-white">
            ✓
          </span>
          <p className="text-xs font-bold text-emerald-900">图纸已复核完成</p>
        </div>
        <p className="mt-1 text-xs text-emerald-800 leading-relaxed">
          该零件图所有字段已确认，可直接作为可追溯的报价基准。
        </p>
        <button
          type="button"
          disabled={pending}
          onClick={() => {
            void onReopen();
          }}
          className="btn-secondary-capsule mt-3 h-8 px-4 text-xs font-medium text-emerald-900 border-emerald-200 cursor-pointer disabled:opacity-50"
        >
          {pending ? "正在打开…" : "重新打开修改"}
        </button>
        {error ? (
          <p className="mt-2 text-xs text-red-600" role="alert">
            ⚠ {error}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="glass-card-subtle rounded-2xl border border-blue-200/60 bg-blue-50/50 p-4 shadow-2xs">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold text-slate-900">
          {pendingCount === 0 ? "✓ 待确认项已全部核对完毕" : `还剩 ${pendingCount} 项待确认`}
        </p>
        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold text-blue-700">
          {pendingCount === 0 ? "可完成" : "复核中"}
        </span>
      </div>
      {pendingCount > 0 ? (
        <p className="mt-1 text-xs text-slate-500">待核对项：{pendingLabels.join("、")}</p>
      ) : (
        <p className="mt-1 text-xs text-slate-500">字段无遗漏，可将图纸状态标记为「已复核」。</p>
      )}
      <button
        type="button"
        disabled={pending}
        onClick={() => {
          void onComplete();
        }}
        className="btn-primary-capsule mt-3 h-8.5 px-4 text-xs text-white cursor-pointer disabled:opacity-50"
      >
        {pending ? "正在标记…" : "标记为已复核"}
      </button>
      {error ? (
        <p className="mt-2 text-xs text-red-600" role="alert">
          ⚠ {error}
        </p>
      ) : null}
    </div>
  );
}
