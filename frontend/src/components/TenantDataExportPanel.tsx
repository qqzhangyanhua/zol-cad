"use client";

import { useState } from "react";

import { readErrorDetail } from "@/lib/types";

function filenameFromDisposition(header: string | null): string {
  if (header === null) {
    return "本厂数据导出.zip";
  }
  const starred = /filename\*=UTF-8''([^;]+)/i.exec(header);
  if (starred?.[1]) {
    return decodeURIComponent(starred[1]);
  }
  const quoted = /filename="([^"]+)"/i.exec(header);
  if (quoted?.[1]) {
    return quoted[1];
  }
  return "本厂数据导出.zip";
}

export function TenantDataExportPanel() {
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function exportArchive(): Promise<void> {
    setPending(true);
    setError(null);
    const response = await fetch("/api/admin/tenant-data/export");
    if (!response.ok) {
      const payload: unknown = await response.json().catch(() => null);
      setError(readErrorDetail(payload) ?? "导出本厂数据失败");
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
          <h2 className="text-sm font-semibold text-stone-900">导出本厂全部数据</h2>
          <p className="mt-1 text-xs leading-5 text-stone-500">
            一次带走本厂零件图原文件、提取结果、复核结果、风险标签、报价任务和修正记录。压缩包里是
            JSON / CSV / 原图，可用表格软件或程序直接打开，不是黑盒。
          </p>
        </div>
        <button
          type="button"
          disabled={pending}
          onClick={() => {
            void exportArchive();
          }}
          className="h-10 rounded-lg bg-stone-900 px-4 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-60"
        >
          {pending ? "正在导出…" : "导出本厂数据"}
        </button>
      </div>
      {error ? (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
