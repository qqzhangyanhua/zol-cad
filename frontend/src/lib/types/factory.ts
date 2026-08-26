import { isUserRole, type UserRole } from "@/lib/types/auth";
import { isRecord } from "@/lib/types/guard";
import {
  isPartDrawingStatus,
  isQualityGrade,
  type PartDrawingStatus,
  type QualityGrade,
} from "@/lib/types/part-drawing";
import { isRiskLabelName, type RiskLabelName } from "@/lib/types/risk";

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

export type TenantDeleteChallenge = {
  confirm_token: string;
  confirm_phrase: string;
  expires_at: string;
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
