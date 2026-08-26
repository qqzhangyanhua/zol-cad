import type { InFlightPartDrawingStatus, PartDrawingStatus } from "@/lib/types";
import { isInFlightPartDrawingStatus } from "@/lib/types";

export const EXTRACTION_LONG_WAIT_SECONDS = 60;

export const EXTRACTION_LONG_WAIT_HINT =
  "仍在处理中，可稍后回来查看。处理时间因图纸而异，这不代表已经卡住。";

export type ExtractionProgressStatus = InFlightPartDrawingStatus | "已分级";

export type ExtractionProgressCopy = {
  title: string;
  body: string;
};

export function isExtractionProgressStatus(
  status: PartDrawingStatus,
): status is ExtractionProgressStatus {
  return isInFlightPartDrawingStatus(status) || status === "已分级";
}

export function extractionProgressCopy(status: ExtractionProgressStatus): ExtractionProgressCopy {
  switch (status) {
    case "已上传":
      return {
        title: "等待处理",
        body: "零件图已收到，正在排队等待系统开始处理。请稍候，完成后会在左侧预填表单。",
      };
    case "分级中":
      return {
        title: "正在评估图纸质量",
        body: "系统正在做图纸质量分级。请稍候，完成后会在左侧预填表单。",
      };
    case "已分级":
      return {
        title: "正在启动读图取数",
        body: "图纸质量分级已完成，系统正在开始读图取数。请稍候，完成后会在左侧预填表单。",
      };
    case "提取中":
      return {
        title: "正在读图取数",
        body: "系统正在从零件图中提取标题栏、关键尺寸与技术要求。请稍候，完成后会在左侧预填表单。",
      };
    default: {
      const exhaustive: never = status;
      return exhaustive;
    }
  }
}

export function elapsedSecondsSince(startedAt: string, nowMs: number): number {
  const startedMs = Date.parse(startedAt);
  if (!Number.isFinite(startedMs)) {
    return 0;
  }
  return Math.max(0, Math.floor((nowMs - startedMs) / 1000));
}

export function isLongExtractionWait(elapsedSeconds: number): boolean {
  return elapsedSeconds >= EXTRACTION_LONG_WAIT_SECONDS;
}
