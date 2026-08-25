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
};

export type PartDrawingList = {
  items: PartDrawing[];
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

export function parsePartDrawingList(data: unknown): PartDrawingList {
  if (typeof data !== "object" || data === null) {
    throw new Error("零件图列表响应格式不正确");
  }
  const record = data as Record<string, unknown>;
  if (!Array.isArray(record.items)) {
    throw new Error("零件图列表响应格式不正确");
  }
  const items: PartDrawing[] = record.items.map((item) => {
    if (typeof item !== "object" || item === null) {
      throw new Error("零件图列表响应格式不正确");
    }
    const row = item as Record<string, unknown>;
    if (
      typeof row.id !== "string" ||
      typeof row.original_filename !== "string" ||
      typeof row.uploaded_at !== "string"
    ) {
      throw new Error("零件图列表响应格式不正确");
    }
    return {
      id: row.id,
      original_filename: row.original_filename,
      uploaded_at: row.uploaded_at,
    };
  });
  return { items };
}

export function readErrorDetail(data: unknown): string | null {
  if (typeof data !== "object" || data === null) {
    return null;
  }
  const record = data as Record<string, unknown>;
  return typeof record.detail === "string" ? record.detail : null;
}
