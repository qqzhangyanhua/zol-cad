"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { readErrorDetail } from "@/lib/types";

type ContinueDespiteQualityButtonProps = {
  drawingId: string;
};

export function ContinueDespiteQualityButton({ drawingId }: ContinueDespiteQualityButtonProps) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onContinue(): Promise<void> {
    if (pending) {
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch(`/api/part-drawings/${drawingId}/continue-despite-quality`, {
      method: "POST",
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "无法仍然继续");
      setPending(false);
      return;
    }
    router.refresh();
    setPending(false);
  }

  return (
    <div>
      <button
        type="button"
        disabled={pending}
        onClick={() => {
          void onContinue();
        }}
        className="h-9 rounded-lg border border-red-300 bg-white px-3 text-sm font-medium text-red-900 hover:bg-red-50 disabled:opacity-50"
      >
        {pending ? "处理中…" : "仍然继续"}
      </button>
      {error ? (
        <p className="mt-2 text-xs text-red-700" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
