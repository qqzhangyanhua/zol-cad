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
  return (
    <div className="glass-card overflow-hidden flex min-h-[38rem] flex-col lg:flex-row backdrop-blur-xl">
      <aside className="w-full overflow-y-auto border-b border-slate-200/80 bg-white/40 p-5 lg:w-[28rem] lg:border-b-0 lg:border-r">
        {drawing.status === "已分级" && drawing.auto_prefill_allowed ? (
          <AutoStartExtraction drawingId={drawing.id} />
        ) : null}
        {drawing.status === "已上传" ||
        drawing.status === "分级中" ||
        drawing.status === "提取中" ? (
          <ExtractionInProgress drawingId={drawing.id} />
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
      <div className="flex min-h-[32rem] min-w-0 flex-1 flex-col bg-slate-100/50">
        <OriginalDrawingViewer
          src={originalSrc}
          contentType={original.content_type}
          filename={original.original_filename}
        />
      </div>
    </div>
  );
}
