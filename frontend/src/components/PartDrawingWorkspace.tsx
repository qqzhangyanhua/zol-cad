import { AutoStartExtraction } from "@/components/AutoStartExtraction";
import { ExtractionFailedPanel } from "@/components/ExtractionFailedPanel";
import { ExtractionForm } from "@/components/ExtractionForm";
import { ExtractionInProgress } from "@/components/ExtractionInProgress";
import { OriginalDrawingViewer } from "@/components/OriginalDrawingViewer";
import { RiskLabelList } from "@/components/RiskLabelList";
import type { OriginalAccess, PartDrawing } from "@/lib/types";

type PartDrawingWorkspaceProps = {
  drawing: PartDrawing;
  originalSrc: string;
  original: OriginalAccess;
};

export function PartDrawingWorkspace({
  drawing,
  originalSrc,
  original,
}: PartDrawingWorkspaceProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
      <aside className="min-h-0 w-full overflow-y-auto border-b border-stone-200 bg-stone-50 px-6 py-5 lg:w-[28rem] lg:border-b-0 lg:border-r">
        {drawing.status === "已分级" && drawing.auto_prefill_allowed ? (
          <AutoStartExtraction drawingId={drawing.id} />
        ) : null}
        {drawing.status === "提取中" ? <ExtractionInProgress drawingId={drawing.id} /> : null}
        {drawing.status === "提取失败" && drawing.extraction_failure_reason ? (
          <ExtractionFailedPanel
            drawingId={drawing.id}
            reason={drawing.extraction_failure_reason}
          />
        ) : null}
        {drawing.status === "已提取" ? (
          <div className="mt-5">
            <RiskLabelList
              labels={drawing.risk_labels}
              emptyMessage={drawing.no_judgable_risk_message}
            />
            <ExtractionForm fields={drawing.extracted_fields} />
          </div>
        ) : null}
        {drawing.status === "提取失败" ? (
          <div className="mt-5">
            <ExtractionForm fields={drawing.extracted_fields} />
          </div>
        ) : null}
      </aside>
      <div className="flex min-h-[28rem] min-w-0 flex-1 flex-col">
        <OriginalDrawingViewer
          src={originalSrc}
          contentType={original.content_type}
          filename={original.original_filename}
        />
      </div>
    </div>
  );
}
