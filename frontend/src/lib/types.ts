export type UserRole = "quoter" | "admin";

export type CurrentUser = {
  username: string;
  factory_name: string;
  role: UserRole;
};

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

export const RISK_LABEL_NAMES = ["高精度", "深孔", "薄壁", "细长"] as const;
export type RiskLabelName = (typeof RISK_LABEL_NAMES)[number];

export type RiskLabel = {
  name: RiskLabelName;
  rule_id: string;
  triggering_value: string;
  reason: string;
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

export type CorrectionRecord = {
  id: string;
  part_drawing_id: string;
  field_key: string;
  field_type: string;
  old_value: string | null;
  new_value: string | null;
  actor_user_id: string;
  occurred_at: string;
};

export type CorrectionRecordList = {
  items: CorrectionRecord[];
};

export type CorrectionFieldTypeStat = {
  field_type: string;
  correction_count: number;
};

export type CorrectionStats = {
  items: CorrectionFieldTypeStat[];
  purpose: string;
};

export type OriginalAccess = {
  url: string;
  expires_at: string;
  content_type: string;
  original_filename: string;
  page_count: number;
  selected_page: number;
};

export type ApiErrorBody = {
  detail: string;
};

export function isUserRole(value: string): value is UserRole {
  return value === "quoter" || value === "admin";
}

export function parseCurrentUser(data: unknown): CurrentUser {
  if (typeof data !== "object" || data === null) {
    throw new Error("当前用户响应格式不正确");
  }
  const record = data as Record<string, unknown>;
  if (
    typeof record.username !== "string" ||
    typeof record.factory_name !== "string" ||
    typeof record.role !== "string" ||
    !isUserRole(record.role)
  ) {
    throw new Error("当前用户响应格式不正确");
  }
  return {
    username: record.username,
    factory_name: record.factory_name,
    role: record.role,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isQualityGrade(value: unknown): value is QualityGrade {
  return value === "清晰" || value === "一般" || value === "差";
}

function isPartDrawingStatus(value: unknown): value is PartDrawingStatus {
  return (PART_DRAWING_STATUSES as readonly string[]).includes(value as string);
}

function isFieldCategory(value: unknown): value is FieldCategory {
  return (FIELD_CATEGORIES as readonly string[]).includes(value as string);
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

function isFieldSource(value: unknown): value is FieldSource {
  return (FIELD_SOURCES as readonly string[]).includes(value as string);
}

function isRiskLabelName(value: unknown): value is RiskLabelName {
  return (RISK_LABEL_NAMES as readonly string[]).includes(value as string);
}

function parseRiskLabel(data: unknown): RiskLabel {
  if (!isRecord(data)) {
    throw new Error("风险标签响应格式不正确");
  }
  if (
    !isRiskLabelName(data.name) ||
    typeof data.rule_id !== "string" ||
    typeof data.triggering_value !== "string" ||
    typeof data.reason !== "string"
  ) {
    throw new Error("风险标签响应格式不正确");
  }
  return {
    name: data.name,
    rule_id: data.rule_id,
    triggering_value: data.triggering_value,
    reason: data.reason,
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

export function parseCorrectionRecord(data: unknown): CorrectionRecord {
  if (!isRecord(data)) {
    throw new Error("修正记录响应格式不正确");
  }
  if (
    typeof data.id !== "string" ||
    typeof data.part_drawing_id !== "string" ||
    typeof data.field_key !== "string" ||
    typeof data.field_type !== "string" ||
    !(data.old_value === null || typeof data.old_value === "string") ||
    !(data.new_value === null || typeof data.new_value === "string") ||
    typeof data.actor_user_id !== "string" ||
    typeof data.occurred_at !== "string"
  ) {
    throw new Error("修正记录响应格式不正确");
  }
  return {
    id: data.id,
    part_drawing_id: data.part_drawing_id,
    field_key: data.field_key,
    field_type: data.field_type,
    old_value: data.old_value,
    new_value: data.new_value,
    actor_user_id: data.actor_user_id,
    occurred_at: data.occurred_at,
  };
}

export function parseCorrectionRecordList(data: unknown): CorrectionRecordList {
  if (!isRecord(data) || !Array.isArray(data.items)) {
    throw new Error("修正记录列表响应格式不正确");
  }
  return { items: data.items.map(parseCorrectionRecord) };
}

export function parseCorrectionStats(data: unknown): CorrectionStats {
  if (!isRecord(data) || !Array.isArray(data.items) || typeof data.purpose !== "string") {
    throw new Error("修正记录统计响应格式不正确");
  }
  const items: CorrectionFieldTypeStat[] = data.items.map((item) => {
    if (
      !isRecord(item) ||
      typeof item.field_type !== "string" ||
      typeof item.correction_count !== "number"
    ) {
      throw new Error("修正记录统计响应格式不正确");
    }
    return { field_type: item.field_type, correction_count: item.correction_count };
  });
  return { items, purpose: data.purpose };
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

export function readErrorDetail(data: unknown): string | null {
  if (!isRecord(data)) {
    return null;
  }
  return typeof data.detail === "string" ? data.detail : null;
}

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

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

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

export const QUOTE_TASK_REVIEW_STATUSES = ["无零件图", "复核未完成", "已复核"] as const;
export type QuoteTaskReviewStatus = (typeof QUOTE_TASK_REVIEW_STATUSES)[number];

export type QuoteTaskSummary = {
  id: string;
  name: string;
  customer_name: string;
  created_at: string;
  review_status: QuoteTaskReviewStatus;
  drawing_count: number;
};

export type QuoteTaskList = {
  items: QuoteTaskSummary[];
};

export type QuoteTaskDetail = {
  id: string;
  name: string;
  customer_name: string;
  created_at: string;
  review_status: QuoteTaskReviewStatus;
  drawings: PartDrawing[];
};

export type QuoteTaskSearchParams = {
  customer_name?: string;
  created_from?: string;
  created_to?: string;
  review_status?: QuoteTaskReviewStatus | "";
};

function isQuoteTaskReviewStatus(value: unknown): value is QuoteTaskReviewStatus {
  return (QUOTE_TASK_REVIEW_STATUSES as readonly string[]).includes(value as string);
}

export function parseQuoteTaskSummary(data: unknown): QuoteTaskSummary {
  if (!isRecord(data)) {
    throw new Error("报价任务响应格式不正确");
  }
  if (
    typeof data.id !== "string" ||
    typeof data.name !== "string" ||
    typeof data.customer_name !== "string" ||
    typeof data.created_at !== "string" ||
    !isQuoteTaskReviewStatus(data.review_status) ||
    typeof data.drawing_count !== "number"
  ) {
    throw new Error("报价任务响应格式不正确");
  }
  return {
    id: data.id,
    name: data.name,
    customer_name: data.customer_name,
    created_at: data.created_at,
    review_status: data.review_status,
    drawing_count: data.drawing_count,
  };
}

export function parseQuoteTaskList(data: unknown): QuoteTaskList {
  if (!isRecord(data) || !Array.isArray(data.items)) {
    throw new Error("报价任务列表响应格式不正确");
  }
  return { items: data.items.map(parseQuoteTaskSummary) };
}

export function parseQuoteTaskDetail(data: unknown): QuoteTaskDetail {
  if (!isRecord(data)) {
    throw new Error("报价任务详情响应格式不正确");
  }
  if (
    typeof data.id !== "string" ||
    typeof data.name !== "string" ||
    typeof data.customer_name !== "string" ||
    typeof data.created_at !== "string" ||
    !isQuoteTaskReviewStatus(data.review_status) ||
    !Array.isArray(data.drawings)
  ) {
    throw new Error("报价任务详情响应格式不正确");
  }
  return {
    id: data.id,
    name: data.name,
    customer_name: data.customer_name,
    created_at: data.created_at,
    review_status: data.review_status,
    drawings: data.drawings.map(parsePartDrawing),
  };
}

export function quoteTaskSearchQuery(params: QuoteTaskSearchParams): string {
  const query = new URLSearchParams();
  if (params.customer_name) {
    query.set("customer_name", params.customer_name);
  }
  if (params.created_from) {
    query.set("created_from", params.created_from);
  }
  if (params.created_to) {
    query.set("created_to", params.created_to);
  }
  if (params.review_status) {
    query.set("review_status", params.review_status);
  }
  const encoded = query.toString();
  return encoded === "" ? "" : `?${encoded}`;
}

export type FactoryAccount = {
  id: string;
  username: string;
  role: UserRole;
  created_at: string;
  disabled_at: string | null;
};

export type FactoryAccountList = {
  items: FactoryAccount[];
};

export type FactoryPreferences = {
  common_materials: string[];
  risk_label_priority: RiskLabelName[];
};

export type RiskRule = {
  rule_id: string;
  label_name: RiskLabelName;
  threshold: string;
  description: string;
  provisional: boolean;
};

export type RiskRuleList = {
  items: RiskRule[];
};

export type FactoryProcessingRecord = {
  part_drawing_id: string;
  original_filename: string;
  uploaded_at: string;
  status: PartDrawingStatus;
  uploaded_by_user_id: string | null;
  uploaded_by_username: string | null;
  quote_task_id: string | null;
  quality_grade: QualityGrade | null;
};

export type FactoryProcessingRecordList = {
  items: FactoryProcessingRecord[];
};

function isFactoryAccount(data: unknown): data is FactoryAccount {
  if (!isRecord(data)) {
    return false;
  }
  return (
    typeof data.id === "string" &&
    typeof data.username === "string" &&
    typeof data.role === "string" &&
    isUserRole(data.role) &&
    typeof data.created_at === "string" &&
    (data.disabled_at === null || typeof data.disabled_at === "string")
  );
}

export function parseFactoryAccount(data: unknown): FactoryAccount {
  if (!isFactoryAccount(data)) {
    throw new Error("账号响应格式不正确");
  }
  return {
    id: data.id,
    username: data.username,
    role: data.role,
    created_at: data.created_at,
    disabled_at: data.disabled_at,
  };
}

export function parseFactoryAccountList(data: unknown): FactoryAccountList {
  if (!isRecord(data) || !Array.isArray(data.items)) {
    throw new Error("账号列表响应格式不正确");
  }
  return { items: data.items.map(parseFactoryAccount) };
}

export function parseFactoryPreferences(data: unknown): FactoryPreferences {
  if (!isRecord(data) || !Array.isArray(data.common_materials) || !Array.isArray(data.risk_label_priority)) {
    throw new Error("本厂偏好响应格式不正确");
  }
  if (!data.common_materials.every((item) => typeof item === "string")) {
    throw new Error("本厂偏好响应格式不正确");
  }
  if (!data.risk_label_priority.every((item) => isRiskLabelName(item))) {
    throw new Error("本厂偏好响应格式不正确");
  }
  return {
    common_materials: data.common_materials,
    risk_label_priority: data.risk_label_priority,
  };
}

export function parseRiskRuleList(data: unknown): RiskRuleList {
  if (!isRecord(data) || !Array.isArray(data.items)) {
    throw new Error("风险规则响应格式不正确");
  }
  return {
    items: data.items.map((item) => {
      if (
        !isRecord(item) ||
        typeof item.rule_id !== "string" ||
        !isRiskLabelName(item.label_name) ||
        typeof item.threshold !== "string" ||
        typeof item.description !== "string" ||
        typeof item.provisional !== "boolean"
      ) {
        throw new Error("风险规则响应格式不正确");
      }
      return {
        rule_id: item.rule_id,
        label_name: item.label_name,
        threshold: item.threshold,
        description: item.description,
        provisional: item.provisional,
      };
    }),
  };
}

export function parseFactoryProcessingRecordList(data: unknown): FactoryProcessingRecordList {
  if (!isRecord(data) || !Array.isArray(data.items)) {
    throw new Error("处理记录响应格式不正确");
  }
  return {
    items: data.items.map((item) => {
      if (
        !isRecord(item) ||
        typeof item.part_drawing_id !== "string" ||
        typeof item.original_filename !== "string" ||
        typeof item.uploaded_at !== "string" ||
        !isPartDrawingStatus(item.status) ||
        !(item.uploaded_by_user_id === null || typeof item.uploaded_by_user_id === "string") ||
        !(item.uploaded_by_username === null || typeof item.uploaded_by_username === "string") ||
        !(item.quote_task_id === null || typeof item.quote_task_id === "string") ||
        !(item.quality_grade === null || isQualityGrade(item.quality_grade))
      ) {
        throw new Error("处理记录响应格式不正确");
      }
      return {
        part_drawing_id: item.part_drawing_id,
        original_filename: item.original_filename,
        uploaded_at: item.uploaded_at,
        status: item.status,
        uploaded_by_user_id: item.uploaded_by_user_id,
        uploaded_by_username: item.uploaded_by_username,
        quote_task_id: item.quote_task_id,
        quality_grade: item.quality_grade,
      };
    }),
  };
}

export type TenantDeleteChallenge = {
  confirm_token: string;
  confirm_phrase: string;
  expires_at: string;
};

export function parseTenantDeleteChallenge(data: unknown): TenantDeleteChallenge {
  if (!isRecord(data)) {
    throw new Error("删除确认响应格式不正确");
  }
  if (
    typeof data.confirm_token !== "string" ||
    typeof data.confirm_phrase !== "string" ||
    typeof data.expires_at !== "string"
  ) {
    throw new Error("删除确认响应格式不正确");
  }
  return {
    confirm_token: data.confirm_token,
    confirm_phrase: data.confirm_phrase,
    expires_at: data.expires_at,
  };
}

export function sortRiskLabels(labels: RiskLabel[], priority: readonly RiskLabelName[]): RiskLabel[] {
  const rank = new Map(priority.map((name, index) => [name, index]));
  return [...labels].sort((left, right) => {
    const leftRank = rank.get(left.name) ?? priority.length;
    const rightRank = rank.get(right.name) ?? priority.length;
    return leftRank - rightRank;
  });
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
