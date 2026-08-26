import { isRecord } from "@/lib/types/guard";
import { parsePartDrawing, type PartDrawing } from "@/lib/types/part-drawing";

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
  unreviewed_member_count: number;
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
    typeof data.unreviewed_member_count !== "number" ||
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
    unreviewed_member_count: data.unreviewed_member_count,
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
