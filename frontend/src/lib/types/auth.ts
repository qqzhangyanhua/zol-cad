import { isRecord } from "@/lib/types/guard";

export type UserRole = "quoter" | "admin";

export type CurrentUser = {
  username: string;
  factory_name: string;
  role: UserRole;
};

export function isUserRole(value: string): value is UserRole {
  return value === "quoter" || value === "admin";
}

export function parseCurrentUser(data: unknown): CurrentUser {
  if (!isRecord(data)) {
    throw new Error("当前用户响应格式不正确");
  }
  if (
    typeof data.username !== "string" ||
    typeof data.factory_name !== "string" ||
    typeof data.role !== "string" ||
    !isUserRole(data.role)
  ) {
    throw new Error("当前用户响应格式不正确");
  }
  return {
    username: data.username,
    factory_name: data.factory_name,
    role: data.role,
  };
}
