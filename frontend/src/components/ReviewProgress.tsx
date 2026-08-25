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
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-3">
        <p className="text-sm font-medium text-emerald-900">已复核</p>
        <p className="mt-1 text-xs text-emerald-800">这张零件图已成为可追溯的报价依据。</p>
        <button
          type="button"
          disabled={pending}
          onClick={() => {
            void onReopen();
          }}
          className="mt-3 h-9 rounded-lg border border-emerald-300 bg-white px-3 text-sm font-medium text-emerald-900 hover:bg-emerald-100 disabled:opacity-50"
        >
          {pending ? "正在打开…" : "重新打开修改"}
        </button>
        {error ? (
          <p className="mt-2 text-xs text-red-700" role="alert">
            {error}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-stone-200 bg-white px-3 py-3">
      <p className="text-sm font-medium text-stone-900">
        {pendingCount === 0 ? "需确认项已全部处理" : `还剩 ${pendingCount} 项待处理`}
      </p>
      {pendingCount > 0 ? (
        <p className="mt-1 text-xs text-stone-500">待确认：{pendingLabels.join("、")}</p>
      ) : (
        <p className="mt-1 text-xs text-stone-500">可以标记这张零件图为已复核。</p>
      )}
      <button
        type="button"
        disabled={pending}
        onClick={() => {
          void onComplete();
        }}
        className="mt-3 h-9 rounded-lg bg-stone-900 px-3 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-50"
      >
        {pending ? "正在标记…" : "标记已复核"}
      </button>
      {error ? (
        <p className="mt-2 text-xs text-red-700" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
