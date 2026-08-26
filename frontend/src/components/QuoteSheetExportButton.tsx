"use client";

import { useState } from "react";
import { ExportIcon } from "@/components/Icons";
import { readErrorDetail, type QuoteTaskDetail } from "@/lib/types";

type QuoteSheetExportButtonProps = {
  task: QuoteTaskDetail;
};

type QuoteSheetExportFormat = "xlsx" | "csv";

const FORMAT_FALLBACK_NAME: Record<QuoteSheetExportFormat, string> = {
  xlsx: "报价底稿.xlsx",
  csv: "报价底稿.csv",
};

function filenameFromDisposition(header: string | null, fileFormat: QuoteSheetExportFormat): string {
  if (header === null) {
    return FORMAT_FALLBACK_NAME[fileFormat];
  }
  const starred = /filename\*=UTF-8''([^;]+)/i.exec(header);
  if (starred?.[1]) {
    return decodeURIComponent(starred[1]);
  }
  const quoted = /filename="([^"]+)"/i.exec(header);
  if (quoted?.[1]) {
    return quoted[1];
  }
  return FORMAT_FALLBACK_NAME[fileFormat];
}

function unreviewedExportWarning(task: QuoteTaskDetail): string | null {
  const unfinished = task.drawings.filter((drawing) => drawing.status !== "已复核");
  if (task.unreviewed_member_count <= 0 && unfinished.length === 0) {
    return null;
  }
  const count = Math.max(task.unreviewed_member_count, unfinished.length);
  if (task.unreviewed_member_count > unfinished.length) {
    return `本任务中有 ${count} 个零件尚未完成复核，其中部分不由你处理`;
  }
  const names = unfinished.map((drawing) => drawing.original_filename).join("、");
  return `尚有未完成复核的零件图：${names}。若需出具最终报价，请先完成全部图纸复核。`;
}

export function QuoteSheetExportButton({ task }: QuoteSheetExportButtonProps) {
  const [error, setError] = useState<string | null>(null);
  const [pendingFormat, setPendingFormat] = useState<QuoteSheetExportFormat | null>(null);
  const warning = unreviewedExportWarning(task);
  const blocked = warning !== null;
  const pending = pendingFormat !== null;

  async function exportSheet(fileFormat: QuoteSheetExportFormat): Promise<void> {
    if (blocked) {
      return;
    }
    setPendingFormat(fileFormat);
    setError(null);
    const response = await fetch(`/api/quote-tasks/${task.id}/quote-sheet?format=${fileFormat}`);
    if (!response.ok) {
      const payload: unknown = await response.json().catch(() => null);
      setError(readErrorDetail(payload) ?? "导出报价底稿失败");
      setPendingFormat(null);
      return;
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filenameFromDisposition(response.headers.get("content-disposition"), fileFormat);
    link.click();
    URL.revokeObjectURL(objectUrl);
    setPendingFormat(null);
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
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={pending || blocked}
            onClick={() => {
              void exportSheet("xlsx");
            }}
            className="btn-primary-capsule h-9 gap-1.5 px-4 text-xs text-white cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
          >
            <ExportIcon className="h-3.5 w-3.5" />
            {pendingFormat === "xlsx" ? "正在导出…" : "导出 Excel"}
          </button>
          <button
            type="button"
            disabled={pending || blocked}
            onClick={() => {
              void exportSheet("csv");
            }}
            className="btn-secondary-capsule h-9 gap-1.5 px-4 text-xs text-slate-700 cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
          >
            <ExportIcon className="h-3.5 w-3.5" />
            {pendingFormat === "csv" ? "正在导出…" : "导出 CSV"}
          </button>
        </div>
      </div>
      {warning ? (
        <div className="glass-warning-pill mt-3 px-3 py-2 text-xs">⚠ {warning}</div>
      ) : null}
      {error ? (
        <p className="mt-2.5 text-xs text-red-600 font-medium" role="alert">
          ⚠ {error}
        </p>
      ) : null}
    </section>
  );
}
