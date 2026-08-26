import { isRecord } from "@/lib/types/guard";

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
