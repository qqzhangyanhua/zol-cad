import { isFiniteNumber, isRecord } from "@/lib/types/guard";

export type ManualBaseline = {
  id: string;
  part_description: string;
  manual_duration_seconds: number;
  recorded_at: string;
};

export type DrawingProcessingTime = {
  part_drawing_id: string;
  original_filename: string;
  uploaded_at: string;
  reviewed_at: string;
  processing_seconds: number;
  grading_seconds: number | null;
  extraction_seconds: number | null;
  review_seconds: number | null;
};

export type ProcessingTimeComparison = {
  reviewed_count: number;
  excluded_unreviewed_count: number;
  average_processing_seconds: number | null;
  average_grading_seconds: number | null;
  average_extraction_seconds: number | null;
  average_review_seconds: number | null;
  baseline_count: number;
  average_baseline_seconds: number | null;
  saved_seconds: number | null;
  items: DrawingProcessingTime[];
  baselines: ManualBaseline[];
};

function parseManualBaseline(data: unknown): ManualBaseline {
  if (!isRecord(data)) {
    throw new Error("人工基线响应格式不正确");
  }
  if (
    typeof data.id !== "string" ||
    typeof data.part_description !== "string" ||
    !isFiniteNumber(data.manual_duration_seconds) ||
    typeof data.recorded_at !== "string"
  ) {
    throw new Error("人工基线响应格式不正确");
  }
  return {
    id: data.id,
    part_description: data.part_description,
    manual_duration_seconds: data.manual_duration_seconds,
    recorded_at: data.recorded_at,
  };
}

function parseOptionalSeconds(value: unknown): number | null {
  if (value === null) {
    return null;
  }
  if (!isFiniteNumber(value)) {
    throw new Error("处理耗时响应格式不正确");
  }
  return value;
}

function parseDrawingProcessingTime(data: unknown): DrawingProcessingTime {
  if (!isRecord(data)) {
    throw new Error("处理耗时响应格式不正确");
  }
  if (
    typeof data.part_drawing_id !== "string" ||
    typeof data.original_filename !== "string" ||
    typeof data.uploaded_at !== "string" ||
    typeof data.reviewed_at !== "string" ||
    !isFiniteNumber(data.processing_seconds)
  ) {
    throw new Error("处理耗时响应格式不正确");
  }
  return {
    part_drawing_id: data.part_drawing_id,
    original_filename: data.original_filename,
    uploaded_at: data.uploaded_at,
    reviewed_at: data.reviewed_at,
    processing_seconds: data.processing_seconds,
    grading_seconds: parseOptionalSeconds(data.grading_seconds),
    extraction_seconds: parseOptionalSeconds(data.extraction_seconds),
    review_seconds: parseOptionalSeconds(data.review_seconds),
  };
}

export function parseProcessingTimeComparison(data: unknown): ProcessingTimeComparison {
  if (!isRecord(data)) {
    throw new Error("处理耗时对比响应格式不正确");
  }
  if (
    !isFiniteNumber(data.reviewed_count) ||
    !isFiniteNumber(data.excluded_unreviewed_count) ||
    !isFiniteNumber(data.baseline_count) ||
    !Array.isArray(data.items) ||
    !Array.isArray(data.baselines)
  ) {
    throw new Error("处理耗时对比响应格式不正确");
  }
  return {
    reviewed_count: data.reviewed_count,
    excluded_unreviewed_count: data.excluded_unreviewed_count,
    average_processing_seconds: parseOptionalSeconds(data.average_processing_seconds),
    average_grading_seconds: parseOptionalSeconds(data.average_grading_seconds),
    average_extraction_seconds: parseOptionalSeconds(data.average_extraction_seconds),
    average_review_seconds: parseOptionalSeconds(data.average_review_seconds),
    baseline_count: data.baseline_count,
    average_baseline_seconds: parseOptionalSeconds(data.average_baseline_seconds),
    saved_seconds: parseOptionalSeconds(data.saved_seconds),
    items: data.items.map(parseDrawingProcessingTime),
    baselines: data.baselines.map(parseManualBaseline),
  };
}

export function parseManualBaselineResponse(data: unknown): ManualBaseline {
  return parseManualBaseline(data);
}
