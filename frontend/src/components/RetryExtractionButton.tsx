"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { parsePartDrawing, readErrorDetail } from "@/lib/types";

type RetryExtractionButtonProps = {
  drawingId: string;
};

export function RetryExtractionButton({ drawingId }: RetryExtractionButtonProps) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onRetry(): Promise<void> {
    if (pending) {
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch(`/api/part-drawings/${drawingId}/extract`, { method: "POST" });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "重试读图取数失败");
      setPending(false);
      return;
    }
    parsePartDrawing(payload);
    router.refresh();
    setPending(false);
  }

  return (
    <div>
      <button
        type="button"
        disabled={pending}
        onClick={() => {
          void onRetry();
        }}
        className="h-9 rounded-lg bg-stone-900 px-3 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-50"
      >
        {pending ? "正在重试…" : "重试读图取数"}
      </button>
      {error ? (
        <p className="mt-2 text-xs text-red-700" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
