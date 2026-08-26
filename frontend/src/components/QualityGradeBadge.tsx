import type { QualityGrade } from "@/lib/types";

type QualityGradeBadgeProps = {
  grade: QualityGrade | null;
};

const GRADE_CLASS: Record<QualityGrade, string> = {
  清晰: "bg-emerald-50 text-emerald-700 border-emerald-200/60",
  一般: "bg-amber-50 text-amber-800 border-amber-200/60",
  差: "bg-rose-50 text-rose-700 border-rose-200/60",
};

export function QualityGradeBadge({ grade }: QualityGradeBadgeProps) {
  if (grade === null) {
    return <span className="text-[11px] text-slate-400">尚未分级</span>;
  }
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium shadow-2xs ${GRADE_CLASS[grade]}`}>
      {grade}
    </span>
  );
}
