import { isRecord } from "@/lib/types/guard";
import { parseRiskLabel, type RiskLabel } from "@/lib/types/risk";

export const QUALITY_GRADES = ["清晰", "一般", "差"] as const;
export type QualityGrade = (typeof QUALITY_GRADES)[number];

export const PART_DRAWING_STATUSES = [
  "已上传",
  "分级中",
  "已分级",
  "建议人工",
  "不在范围",
  "提取中",
  "已提取",
  "提取失败",
  "复核中",
  "已复核",
] as const;
export type PartDrawingStatus = (typeof PART_DRAWING_STATUSES)[number];

export const IN_FLIGHT_PART_DRAWING_STATUSES = ["已上传", "分级中", "提取中"] as const satisfies readonly PartDrawingStatus[];
export type InFlightPartDrawingStatus = (typeof IN_FLIGHT_PART_DRAWING_STATUSES)[number];

export function isInFlightPartDrawingStatus(
  status: PartDrawingStatus,
): status is InFlightPartDrawingStatus {
  return (IN_FLIGHT_PART_DRAWING_STATUSES as readonly string[]).includes(status);
}

export const FIELD_CATEGORIES = ["标题栏", "关键尺寸", "技术要求"] as const;
export type FieldCategory = (typeof FIELD_CATEGORIES)[number];

export const FIELD_SOURCES = ["extracted", "added"] as const;
export type FieldSource = (typeof FIELD_SOURCES)[number];

export const CRITICAL_DIMENSION_KINDS = [
  { kind: "tightest_tolerance", label: "最严公差" },
  { kind: "max_envelope", label: "最大外形" },
  { kind: "deepest_hole", label: "最深孔" },
  { kind: "thinnest_wall", label: "最薄壁" },
] as const;
export type CriticalDimensionKind = (typeof CRITICAL_DIMENSION_KINDS)[number]["kind"];

export type ExtractedField = {
  key: string;
  label: string;
  value: string | null;
  category: FieldCategory;
  requires_confirmation: boolean;
  confirmed: boolean;
  ignored: boolean;
  source: FieldSource;
};

export type PartDrawing = {
  id: string;
  original_filename: string;
  uploaded_at: string;
  content_type: string;
  byte_size: number;
  page_count: number;
  selected_page: number;
  status: PartDrawingStatus;
  quality_grade: QualityGrade | null;
  is_assembly_or_exploded: boolean;
  low_quality_unreliable: boolean;
  auto_prefill_allowed: boolean;
  quality_grade_disclaimer: string;
  advise_manual_message: string | null;
  out_of_scope_message: string | null;
  low_quality_mark: string | null;
  extracted_fields: ExtractedField[];
  extraction_failure_reason: string | null;
  look_at_drawing_disclaimer: string;
  part_family_id: string;
  is_target_part_family: boolean;
  experimental_mark: string | null;
  risk_labels: RiskLabel[];
  no_judgable_risk_message: string;
  pending_confirmation_count: number;
  pending_confirmation_labels: string[];
  quote_task_id: string | null;
};

export type PartDrawingList = {
  items: PartDrawing[];
};

export type RejectedUpload = {
  original_filename: string;
  detail: string;
};

export type UploadPartDrawingsResult = {
  items: PartDrawing[];
  rejected: RejectedUpload[];
};

export type OriginalAccess = {
  url: string;
  expires_at: string;
  content_type: string;
  original_filename: string;
  page_count: number;
  selected_page: number;
};

export function isQualityGrade(value: unknown): value is QualityGrade {
  return value === "清晰" || value === "一般" || value === "差";
}

export function isPartDrawingStatus(value: unknown): value is PartDrawingStatus {
  return (PART_DRAWING_STATUSES as readonly string[]).includes(value as string);
}

function isFieldCategory(value: unknown): value is FieldCategory {
  return (FIELD_CATEGORIES as readonly string[]).includes(value as string);
}

function isFieldSource(value: unknown): value is FieldSource {
  return (FIELD_SOURCES as readonly string[]).includes(value as string);
}

function parseExtractedField(data: unknown): ExtractedField {
  if (!isRecord(data)) {
    throw new Error("提取字段响应格式不正确");
  }
  if (
    typeof data.key !== "string" ||
    typeof data.label !== "string" ||
    !(data.value === null || typeof data.value === "string") ||
    !isFieldCategory(data.category) ||
    typeof data.requires_confirmation !== "boolean" ||
    typeof data.confirmed !== "boolean" ||
    typeof data.ignored !== "boolean" ||
    !isFieldSource(data.source)
  ) {
    throw new Error("提取字段响应格式不正确");
  }
  return {
    key: data.key,
    label: data.label,
    value: data.value,
    category: data.category,
    requires_confirmation: data.requires_confirmation,
    confirmed: data.confirmed,
    ignored: data.ignored,
    source: data.source,
  };
}

export function parsePartDrawing(data: unknown): PartDrawing {
  if (!isRecord(data)) {
    throw new Error("零件图响应格式不正确");
  }
  if (
    typeof data.id !== "string" ||
    typeof data.original_filename !== "string" ||
    typeof data.uploaded_at !== "string" ||
    typeof data.content_type !== "string" ||
    typeof data.byte_size !== "number" ||
    typeof data.page_count !== "number" ||
    typeof data.selected_page !== "number" ||
    !isPartDrawingStatus(data.status) ||
    !(data.quality_grade === null || isQualityGrade(data.quality_grade)) ||
    typeof data.is_assembly_or_exploded !== "boolean" ||
    typeof data.low_quality_unreliable !== "boolean" ||
    typeof data.auto_prefill_allowed !== "boolean" ||
    typeof data.quality_grade_disclaimer !== "string" ||
    !(data.advise_manual_message === null || typeof data.advise_manual_message === "string") ||
    !(data.out_of_scope_message === null || typeof data.out_of_scope_message === "string") ||
    !(data.low_quality_mark === null || typeof data.low_quality_mark === "string") ||
    !Array.isArray(data.extracted_fields) ||
    !(data.extraction_failure_reason === null || typeof data.extraction_failure_reason === "string") ||
    typeof data.look_at_drawing_disclaimer !== "string" ||
    typeof data.part_family_id !== "string" ||
    typeof data.is_target_part_family !== "boolean" ||
    !(data.experimental_mark === null || typeof data.experimental_mark === "string") ||
    !Array.isArray(data.risk_labels) ||
    typeof data.no_judgable_risk_message !== "string" ||
    typeof data.pending_confirmation_count !== "number" ||
    !Array.isArray(data.pending_confirmation_labels) ||
    !data.pending_confirmation_labels.every((label) => typeof label === "string") ||
    !(data.quote_task_id === null || typeof data.quote_task_id === "string")
  ) {
    throw new Error("零件图响应格式不正确");
  }
  return {
    id: data.id,
    original_filename: data.original_filename,
    uploaded_at: data.uploaded_at,
    content_type: data.content_type,
    byte_size: data.byte_size,
    page_count: data.page_count,
    selected_page: data.selected_page,
    status: data.status,
    quality_grade: data.quality_grade,
    is_assembly_or_exploded: data.is_assembly_or_exploded,
    low_quality_unreliable: data.low_quality_unreliable,
    auto_prefill_allowed: data.auto_prefill_allowed,
    quality_grade_disclaimer: data.quality_grade_disclaimer,
    advise_manual_message: data.advise_manual_message,
    out_of_scope_message: data.out_of_scope_message,
    low_quality_mark: data.low_quality_mark,
    extracted_fields: data.extracted_fields.map(parseExtractedField),
    extraction_failure_reason: data.extraction_failure_reason,
    look_at_drawing_disclaimer: data.look_at_drawing_disclaimer,
    part_family_id: data.part_family_id,
    is_target_part_family: data.is_target_part_family,
    experimental_mark: data.experimental_mark,
    risk_labels: data.risk_labels.map(parseRiskLabel),
    no_judgable_risk_message: data.no_judgable_risk_message,
    pending_confirmation_count: data.pending_confirmation_count,
    pending_confirmation_labels: data.pending_confirmation_labels.filter(
      (label): label is string => typeof label === "string",
    ),
    quote_task_id: data.quote_task_id,
  };
}

export function parsePartDrawingList(data: unknown): PartDrawingList {
  if (!isRecord(data) || !Array.isArray(data.items)) {
    throw new Error("零件图列表响应格式不正确");
  }
  return { items: data.items.map(parsePartDrawing) };
}

export function parseUploadResult(data: unknown): UploadPartDrawingsResult {
  if (!isRecord(data) || !Array.isArray(data.items) || !Array.isArray(data.rejected)) {
    throw new Error("上传响应格式不正确");
  }
  const rejected: RejectedUpload[] = data.rejected.map((item) => {
    if (!isRecord(item) || typeof item.original_filename !== "string" || typeof item.detail !== "string") {
      throw new Error("上传响应格式不正确");
    }
    return { original_filename: item.original_filename, detail: item.detail };
  });
  return { items: data.items.map(parsePartDrawing), rejected };
}

export function parseOriginalAccess(data: unknown): OriginalAccess {
  if (!isRecord(data)) {
    throw new Error("原图访问响应格式不正确");
  }
  if (
    typeof data.url !== "string" ||
    typeof data.expires_at !== "string" ||
    typeof data.content_type !== "string" ||
    typeof data.original_filename !== "string" ||
    typeof data.page_count !== "number" ||
    typeof data.selected_page !== "number"
  ) {
    throw new Error("原图访问响应格式不正确");
  }
  return {
    url: data.url,
    expires_at: data.expires_at,
    content_type: data.content_type,
    original_filename: data.original_filename,
    page_count: data.page_count,
    selected_page: data.selected_page,
  };
}

export function resolveOriginalSrc(url: string): string {
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  if (url.startsWith("/")) {
    return `/api${url}`;
  }
  return url;
}
