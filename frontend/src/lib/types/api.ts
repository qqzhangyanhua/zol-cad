import { isRecord } from "@/lib/types/guard";

export type ApiErrorBody = {
  detail: string;
};

export function readErrorDetail(data: unknown): string | null {
  if (!isRecord(data)) {
    return null;
  }
  return typeof data.detail === "string" ? data.detail : null;
}
