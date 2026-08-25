export type UserRole = "quoter" | "admin";

export type CurrentUser = {
  username: string;
  factory_name: string;
  role: UserRole;
};

export type PartDrawing = {
  id: string;
  original_filename: string;
  uploaded_at: string;
  content_type: string;
  byte_size: number;
  page_count: number;
  selected_page: number;
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
    typeof data.selected_page !== "number"
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

export function readErrorDetail(data: unknown): string | null {
  if (!isRecord(data)) {
    return null;
  }
  return typeof data.detail === "string" ? data.detail : null;
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
