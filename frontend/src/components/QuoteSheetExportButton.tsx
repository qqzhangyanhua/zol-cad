"use client";

import { useState } from "react";
import { ExportIcon } from "@/components/Icons";
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
    <section className="glass-card p-5 backdrop-blur-xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-slate-900">报价底稿导出</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            一键导出整个报价任务（每个零件对应一行），格式严格符合本厂底稿模板。
          </p>
        </div>
        <button
          type="button"
          disabled={pending}
          onClick={() => {
            void exportSheet();
          }}
          className="btn-primary-capsule h-9 gap-1.5 px-4 text-xs text-white cursor-pointer disabled:opacity-60"
        >
          <ExportIcon className="h-3.5 w-3.5" />
          {pending ? "正在导出…" : "导出报价底稿 (Excel)"}
        </button>
      </div>
      {unfinished.length > 0 ? (
        <div className="glass-warning-pill mt-3 px-3 py-2 text-xs">
          ⚠ 尚有未完成复核的零件图：
          {unfinished.map((drawing) => drawing.original_filename).join("、")}
          。若需出具最终报价，请先完成全部图纸复核。
        </div>
      ) : null}
      {error ? (
        <p className="mt-2.5 text-xs text-red-600 font-medium" role="alert">
          ⚠ {error}
        </p>
      ) : null}
    </section>
  );
}
