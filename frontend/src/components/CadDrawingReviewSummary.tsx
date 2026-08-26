import { AlertTriangleIcon } from "@/components/Icons";
import { PartDrawingStatusBadge } from "@/components/PartDrawingStatusBadge";
import { QualityGradeBadge } from "@/components/QualityGradeBadge";
import type { PartDrawing } from "@/lib/types";

type CadDrawingReviewSummaryProps = {
  drawing: PartDrawing;
};

function extractedValue(drawing: PartDrawing, key: string): string | null {
  const field = drawing.extracted_fields.find((item) => item.key === key);
  if (field === undefined || field.value === null || field.value.trim() === "") {
    return null;
  }
  return field.value;
}

function SummaryField({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="glass-card-subtle p-3">
      <p className="text-xs text-slate-400">{label}</p>
      {value === null ? (
        <p className="mt-1 min-h-6 text-base font-bold text-slate-900" />
      ) : (
        <p className="mt-1 text-base font-bold text-slate-900">{value}</p>
      )}
    </div>
  );
}

export function CadDrawingReviewSummary({ drawing }: CadDrawingReviewSummaryProps) {
  const drawingNo = extractedValue(drawing, "drawing_no");
  const partName = extractedValue(drawing, "part_name");
  const material = extractedValue(drawing, "material");

  return (
    <section className="glass-card relative overflow-hidden p-6 backdrop-blur-xl">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100/80 pb-4">
        <h3 className="text-base font-bold text-slate-900">提取摘要</h3>
        <div className="flex flex-wrap items-center gap-2">
          <PartDrawingStatusBadge status={drawing.status} />
          <QualityGradeBadge grade={drawing.quality_grade} />
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <SummaryField label="图号" value={drawingNo} />
        <SummaryField label="零件名称" value={partName} />
        <SummaryField label="材料" value={material} />
      </div>

      <div className="mt-5">
        <h4 className="text-sm font-bold text-slate-800">风险标签</h4>
        {drawing.risk_labels.length === 0 ? (
          <p role="status" className="mt-3 text-xs leading-relaxed text-slate-600">
            {drawing.no_judgable_risk_message}
          </p>
        ) : (
          <ul className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {drawing.risk_labels.map((label) => (
              <li key={label.rule_id} className="glass-warning-pill p-2.5 text-xs">
                <div className="flex items-center gap-1.5 font-bold text-amber-900">
                  <AlertTriangleIcon className="h-3.5 w-3.5 shrink-0 text-amber-600" />
                  <span className="truncate">{label.name}</span>
                </div>
                <p className="mt-1 truncate text-[11px] text-amber-800/90">{label.triggering_value}</p>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-5 flex justify-end">
        <a
          href="#drawing-workspace"
          className="inline-flex items-center text-xs font-semibold text-blue-600 hover:text-blue-700"
        >
          查看完整提取与复核表单 →
        </a>
      </div>
    </section>
  );
}
