import type { QualityGrade } from "@/lib/types";

type QualityGradeBadgeProps = {
  grade: QualityGrade | null;
};

const GRADE_CLASS: Record<QualityGrade, string> = {
  清晰: "bg-emerald-50 text-emerald-800",
  一般: "bg-amber-50 text-amber-900",
  差: "bg-red-50 text-red-800",
};

export function QualityGradeBadge({ grade }: QualityGradeBadgeProps) {
  if (grade === null) {
    return <span className="text-xs text-stone-400">尚未分级</span>;
  }
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${GRADE_CLASS[grade]}`}>
      {grade}
    </span>
  );
}
