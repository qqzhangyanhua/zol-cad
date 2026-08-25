import { AssemblyOutOfScopeNotice } from "@/components/AssemblyOutOfScopeNotice";
import { ExperimentalMark } from "@/components/ExperimentalMark";
import { LowQualityMark } from "@/components/LowQualityMark";
import { PoorDrawingAdvise } from "@/components/PoorDrawingAdvise";
import { QualityGradeBadge } from "@/components/QualityGradeBadge";
import { QualityGradeDisclaimer } from "@/components/QualityGradeDisclaimer";
import type { PartDrawing } from "@/lib/types";

type PartDrawingQualityPanelProps = {
  drawing: PartDrawing;
};

export function PartDrawingQualityPanel({ drawing }: PartDrawingQualityPanelProps) {
  return (
    <section className="space-y-3 border-b border-stone-200 bg-white px-6 py-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-stone-500">图纸质量分级</span>
        <QualityGradeBadge grade={drawing.quality_grade} />
        <span className="text-xs text-stone-400">{drawing.status}</span>
      </div>
      <QualityGradeDisclaimer text={drawing.quality_grade_disclaimer} />
      {drawing.experimental_mark ? <ExperimentalMark text={drawing.experimental_mark} /> : null}
      {drawing.low_quality_mark ? <LowQualityMark text={drawing.low_quality_mark} /> : null}
      {drawing.out_of_scope_message ? (
        <AssemblyOutOfScopeNotice text={drawing.out_of_scope_message} />
      ) : null}
      {drawing.advise_manual_message ? (
        <PoorDrawingAdvise drawingId={drawing.id} message={drawing.advise_manual_message} />
      ) : null}
    </section>
  );
}
