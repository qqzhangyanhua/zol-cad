"use client";

import { useState } from "react";
import { AutoStartExtraction } from "@/components/AutoStartExtraction";
import { ExtractionFailedPanel } from "@/components/ExtractionFailedPanel";
import { ExtractionForm } from "@/components/ExtractionForm";
import { ExtractionInProgress } from "@/components/ExtractionInProgress";
import { OriginalDrawingViewer } from "@/components/OriginalDrawingViewer";
import { ReviewForm } from "@/components/ReviewForm";
import { RiskLabelList } from "@/components/RiskLabelList";
import type { OriginalAccess, PartDrawing, RiskLabelName } from "@/lib/types";

type PartDrawingWorkspaceProps = {
  drawing: PartDrawing;
  originalSrc: string;
  original: OriginalAccess;
  materialCandidates: string[];
  riskLabelPriority: readonly RiskLabelName[];
};

export function PartDrawingWorkspace({
  drawing,
  originalSrc,
  original,
  materialCandidates,
  riskLabelPriority,
}: PartDrawingWorkspaceProps) {
  const [formOpen, setFormOpen] = useState(true);
  const [drawingOpen, setDrawingOpen] = useState(true);

  return (
    <div className="glass-card flex min-h-0 flex-col overflow-hidden backdrop-blur-xl lg:min-h-[38rem] lg:flex-row">
      <div className="flex gap-2 border-b border-slate-200/80 bg-white/70 px-3 py-2 lg:hidden">
        <button
          type="button"
          aria-expanded={formOpen}
          aria-controls="review-form-pane"
          className="btn-secondary-capsule h-8 flex-1 px-3 text-xs text-slate-700"
          onClick={() => {
            setFormOpen((current) => !current);
          }}
        >
          {formOpen ? "收起复核表单" : "展开复核表单"}
        </button>
        <button
          type="button"
          aria-expanded={drawingOpen}
          aria-controls="original-drawing-pane"
          className="btn-secondary-capsule h-8 flex-1 px-3 text-xs text-slate-700"
          onClick={() => {
            setDrawingOpen((current) => !current);
          }}
        >
          {drawingOpen ? "收起原图" : "展开原图"}
        </button>
      </div>

      <aside
        id="review-form-pane"
        className={`${formOpen ? "block" : "hidden"} w-full overflow-y-auto border-b border-slate-200/80 bg-white/40 p-4 lg:block lg:w-[28rem] lg:border-b-0 lg:border-r lg:p-5`}
      >
        {drawing.status === "已分级" && drawing.auto_prefill_allowed ? (
          <AutoStartExtraction drawingId={drawing.id} uploadedAt={drawing.uploaded_at} />
        ) : null}
        {drawing.status === "已上传" ||
        drawing.status === "分级中" ||
        drawing.status === "提取中" ? (
          <ExtractionInProgress
            drawingId={drawing.id}
            status={drawing.status}
            uploadedAt={drawing.uploaded_at}
          />
        ) : null}
        {drawing.status === "提取失败" && drawing.extraction_failure_reason ? (
          <ExtractionFailedPanel
            drawingId={drawing.id}
            reason={drawing.extraction_failure_reason}
          />
        ) : null}
        {drawing.status === "已提取" || drawing.status === "复核中" || drawing.status === "已复核" ? (
          <div className="space-y-5">
            <RiskLabelList
              labels={drawing.risk_labels}
              emptyMessage={drawing.no_judgable_risk_message}
              priority={riskLabelPriority}
            />
            <ReviewForm drawing={drawing} materialCandidates={materialCandidates} />
          </div>
        ) : null}
        {drawing.status === "提取失败" ? (
          <div className="mt-5">
            <ExtractionForm fields={drawing.extracted_fields} />
          </div>
        ) : null}
      </aside>
      <div
        id="original-drawing-pane"
        className={`${drawingOpen ? "flex" : "hidden"} min-h-[16rem] min-w-0 flex-1 flex-col bg-slate-100/50 lg:flex lg:min-h-[32rem] ${
          drawingOpen && !formOpen ? "h-[70vh] lg:h-auto" : "h-[40vh] lg:h-auto"
        }`}
      >
        <OriginalDrawingViewer
          src={originalSrc}
          contentType={original.content_type}
          filename={original.original_filename}
        />
      </div>
    </div>
  );
}
