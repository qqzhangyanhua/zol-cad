"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { formatDurationSeconds } from "@/lib/duration";
import {
  EXTRACTION_LONG_WAIT_HINT,
  elapsedSecondsSince,
  extractionProgressCopy,
  isExtractionProgressStatus,
  isLongExtractionWait,
  type ExtractionProgressStatus,
} from "@/lib/extractionProgress";

type ExtractionInProgressProps = {
  drawingId: string;
  status: ExtractionProgressStatus;
  uploadedAt: string;
};

const STAGE_PANEL: Record<ExtractionProgressStatus, string> = {
  已上传: "border-slate-200 bg-slate-50/90",
  分级中: "border-amber-200/80 bg-amber-50/80",
  已分级: "border-sky-200/80 bg-sky-50/80",
  提取中: "border-blue-200/80 bg-blue-50/80",
};

const STAGE_SPINNER: Record<ExtractionProgressStatus, string> = {
  已上传: "border-slate-400 border-t-transparent",
  分级中: "border-amber-500 border-t-transparent",
  已分级: "border-sky-500 border-t-transparent",
  提取中: "border-blue-500 border-t-transparent",
};

function useElapsedSeconds(startedAt: string): number {
  const [nowMs, setNowMs] = useState(() => Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNowMs(Date.now());
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  return elapsedSecondsSince(startedAt, nowMs);
}

export function ExtractionInProgress({
  drawingId,
  status,
  uploadedAt,
}: ExtractionInProgressProps) {
  const router = useRouter();
  const elapsedSeconds = useElapsedSeconds(uploadedAt);
  const copy = extractionProgressCopy(status);
  const longWait = isLongExtractionWait(elapsedSeconds);

  useEffect(() => {
    if (!isExtractionProgressStatus(status)) {
      return;
    }
    const timer = window.setInterval(() => {
      router.refresh();
    }, 1000);
    return () => window.clearInterval(timer);
  }, [drawingId, router, status]);

  return (
    <div
      className={`rounded-lg border px-4 py-6 ${STAGE_PANEL[status]}`}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="flex items-start gap-3">
        <span
          className={`mt-0.5 h-5 w-5 shrink-0 animate-spin rounded-full border-2 ${STAGE_SPINNER[status]}`}
          aria-hidden="true"
        />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-stone-900">{copy.title}</p>
          <p className="mt-1 text-xs leading-5 text-stone-600">{copy.body}</p>
          <p className="mt-3 text-xs font-medium tabular-nums text-stone-700">
            已等待 {formatDurationSeconds(elapsedSeconds)}
          </p>
          {longWait ? (
            <p className="mt-2 text-xs leading-5 text-stone-500">{EXTRACTION_LONG_WAIT_HINT}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
