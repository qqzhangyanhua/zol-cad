import {
  partDrawingStatusGlanceLabel,
  partDrawingStatusTone,
  type PartDrawingStatusTone,
} from "@/lib/partDrawingStatusPresentation";
import type { PartDrawingStatus } from "@/lib/types";

type PartDrawingStatusBadgeProps = {
  status: PartDrawingStatus;
};

const TONE_CLASS: Record<PartDrawingStatusTone, string> = {
  in_progress: "border-amber-200/80 bg-amber-50 text-amber-800",
  extracted: "border-emerald-200/70 bg-emerald-50 text-emerald-800",
  failed: "border-rose-200/80 bg-rose-50 text-rose-800",
  attention: "border-orange-200/80 bg-orange-50 text-orange-800",
  neutral: "border-slate-200 bg-slate-50 text-slate-600",
};

export function PartDrawingStatusBadge({ status }: PartDrawingStatusBadgeProps) {
  const tone = partDrawingStatusTone(status);
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium ${TONE_CLASS[tone]}`}
      aria-label={partDrawingStatusGlanceLabel(status)}
    >
      {tone === "in_progress" ? (
        <span
          className="h-2.5 w-2.5 animate-spin rounded-full border-2 border-current border-t-transparent"
          aria-hidden="true"
        />
      ) : (
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            tone === "extracted" ? "bg-emerald-500" : tone === "failed" ? "bg-rose-500" : "bg-current"
          }`}
          aria-hidden="true"
        />
      )}
      {status}
    </span>
  );
}
