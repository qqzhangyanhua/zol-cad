"use client";

import { useState } from "react";

import { readErrorDetail, type QuoteTaskDetail } from "@/lib/types";

type QuoteSheetExportButtonProps = {
  task: QuoteTaskDetail;
};

function filenameFromDisposition(header: string | null): string {
  if (header === null) {
    return "报价底稿.xlsx";
  }
  const starred = /filename\*=UTF-8''([^;]+)/i.exec(header);
  if (starred?.[1]) {
    return decodeURIComponent(starred[1]);
  }
  const quoted = /filename="([^"]+)"/i.exec(header);
  if (quoted?.[1]) {
    return quoted[1];
  }
  return "报价底稿.xlsx";
}

export function QuoteSheetExportButton({ task }: QuoteSheetExportButtonProps) {
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const unfinished = task.drawings.filter((drawing) => drawing.status !== "已复核");

  async function exportSheet(): Promise<void> {
    setPending(true);
    setError(null);
    const response = await fetch(`/api/quote-tasks/${task.id}/quote-sheet?format=xlsx`);
    if (!response.ok) {
      const payload: unknown = await response.json().catch(() => null);
      setError(readErrorDetail(payload) ?? "导出报价底稿失败");
      setPending(false);
      return;
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filenameFromDisposition(response.headers.get("content-disposition"));
    link.click();
    URL.revokeObjectURL(objectUrl);
    setPending(false);
  }

  return (
    <section className="rounded-xl border border-stone-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-stone-900">报价底稿</h2>
          <p className="mt-1 text-xs text-stone-500">
            一键导出整个报价任务，每个零件一行。列顺序按本厂 onboarding 配好的底稿模板，不在本页改。
          </p>
        </div>
        <button
          type="button"
          disabled={pending}
          onClick={() => {
            void exportSheet();
          }}
          className="h-10 rounded-lg bg-stone-900 px-4 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-60"
        >
          {pending ? "正在导出…" : "导出报价底稿"}
        </button>
      </div>
      {unfinished.length > 0 ? (
        <p className="mt-3 text-xs text-amber-800">
          还有未完成复核的零件图：
          {unfinished.map((drawing) => drawing.original_filename).join("、")}
          。导出会被拦下。
        </p>
      ) : null}
      {error ? (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
