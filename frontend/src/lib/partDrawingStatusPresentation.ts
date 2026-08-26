import { isInFlightPartDrawingStatus, type PartDrawingStatus } from "@/lib/types";

export type PartDrawingStatusTone = "in_progress" | "extracted" | "failed" | "attention" | "neutral";

export function partDrawingStatusTone(status: PartDrawingStatus): PartDrawingStatusTone {
  if (isInFlightPartDrawingStatus(status) || status === "已分级") {
    return "in_progress";
  }
  switch (status) {
    case "已提取":
    case "复核中":
    case "已复核":
      return "extracted";
    case "提取失败":
      return "failed";
    case "建议人工":
    case "不在范围":
      return "attention";
    default: {
      const exhaustive: never = status;
      return exhaustive;
    }
  }
}

export function partDrawingListRowAccent(tone: PartDrawingStatusTone): string {
  switch (tone) {
    case "in_progress":
      return "border-l-2 border-l-amber-400";
    case "extracted":
      return "border-l-2 border-l-emerald-400";
    case "failed":
      return "border-l-2 border-l-rose-400";
    case "attention":
      return "border-l-2 border-l-orange-400";
    case "neutral":
      return "border-l-2 border-l-transparent";
    default: {
      const exhaustive: never = tone;
      return exhaustive;
    }
  }
}

export function partDrawingStatusGlanceLabel(status: PartDrawingStatus): string {
  const tone = partDrawingStatusTone(status);
  if (tone === "in_progress") {
    return `进行中：${status}`;
  }
  if (tone === "failed") {
    return "提取失败";
  }
  return status;
}
