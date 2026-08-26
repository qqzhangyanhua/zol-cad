import { isRecord } from "@/lib/types/guard";

export type HardGateStatus = {
  key: string;
  name: string;
  verdict: string;
  evidence: string;
};

export type DrawingStorageNotice = {
  backend: string;
  location_summary: string;
  notes: string;
};

export type ConfidentialityNotice = {
  ticket_02_closed: boolean;
  ticket_02_status: string;
  adr_status: string;
  adr_path: string;
  research_notes_path: string;
  vendor_selected: boolean;
  selected_vendor: string | null;
  vendor_decision_line: string;
  hard_gates: HardGateStatus[];
  implementation_constraints: string[];
  drawing_storage: DrawingStorageNotice;
  processor_summary: string;
  current_extraction_engine: string;
  used_for_training_statement: string;
  dpa_statement: string;
  caveats: string[];
};

function parseHardGateStatus(data: unknown): HardGateStatus {
  if (!isRecord(data)) {
    throw new Error("保密说明门槛响应格式不正确");
  }
  if (
    typeof data.key !== "string" ||
    typeof data.name !== "string" ||
    typeof data.verdict !== "string" ||
    typeof data.evidence !== "string"
  ) {
    throw new Error("保密说明门槛响应格式不正确");
  }
  return {
    key: data.key,
    name: data.name,
    verdict: data.verdict,
    evidence: data.evidence,
  };
}

export function parseConfidentialityNotice(data: unknown): ConfidentialityNotice {
  if (!isRecord(data)) {
    throw new Error("保密说明响应格式不正确");
  }
  if (
    typeof data.ticket_02_closed !== "boolean" ||
    typeof data.ticket_02_status !== "string" ||
    typeof data.adr_status !== "string" ||
    typeof data.adr_path !== "string" ||
    typeof data.research_notes_path !== "string" ||
    typeof data.vendor_selected !== "boolean" ||
    !(data.selected_vendor === null || typeof data.selected_vendor === "string") ||
    typeof data.vendor_decision_line !== "string" ||
    !Array.isArray(data.hard_gates) ||
    !Array.isArray(data.implementation_constraints) ||
    !data.implementation_constraints.every((item) => typeof item === "string") ||
    !isRecord(data.drawing_storage) ||
    typeof data.drawing_storage.backend !== "string" ||
    typeof data.drawing_storage.location_summary !== "string" ||
    typeof data.drawing_storage.notes !== "string" ||
    typeof data.processor_summary !== "string" ||
    typeof data.current_extraction_engine !== "string" ||
    typeof data.used_for_training_statement !== "string" ||
    typeof data.dpa_statement !== "string" ||
    !Array.isArray(data.caveats) ||
    !data.caveats.every((item) => typeof item === "string")
  ) {
    throw new Error("保密说明响应格式不正确");
  }
  return {
    ticket_02_closed: data.ticket_02_closed,
    ticket_02_status: data.ticket_02_status,
    adr_status: data.adr_status,
    adr_path: data.adr_path,
    research_notes_path: data.research_notes_path,
    vendor_selected: data.vendor_selected,
    selected_vendor: data.selected_vendor,
    vendor_decision_line: data.vendor_decision_line,
    hard_gates: data.hard_gates.map(parseHardGateStatus),
    implementation_constraints: data.implementation_constraints,
    drawing_storage: {
      backend: data.drawing_storage.backend,
      location_summary: data.drawing_storage.location_summary,
      notes: data.drawing_storage.notes,
    },
    processor_summary: data.processor_summary,
    current_extraction_engine: data.current_extraction_engine,
    used_for_training_statement: data.used_for_training_statement,
    dpa_statement: data.dpa_statement,
    caveats: data.caveats,
  };
}
