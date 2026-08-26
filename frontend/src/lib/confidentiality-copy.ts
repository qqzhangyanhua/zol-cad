import type { ConfidentialityNotice, HardGateStatus } from "@/lib/types";

export type ConfidentialityNoticeView = {
  vendorSelected: boolean;
  vendorStatus: string;
  decisionStatus: string;
  extractionEngine: string;
  drawingLocation: string;
  drawingNotes: string;
  processorSummary: string;
  decisionLine: string;
  decisionLineNote: string;
  hardGates: HardGateStatus[];
  trainingStatement: string;
  dpaStatement: string;
  implementationConstraints: string[];
  caveats: string[];
};

const TICKET_AND_ADR = /票\s*0*\d+\s*\/\s*ADR-\d+/gi;
const TICKET_ID = /票\s*0*\d+/g;
const ADR_ID = /ADR-\d+/gi;
const SCRATCH_PATH = /`?\.scratch\/[^`\s，。；、）)]+`?/g;
const ADR_FILE_PATH = /`?docs\/adr\/[^`\s，。；、）)]+`?/g;

function tidyPunctuation(text: string): string {
  return text
    .replace(/[ \t]{2,}/g, " ")
    .replace(/[（(]\s*[）)]/g, "")
    .replace(/[，。；、]\s*[，。；]/g, "。")
    .replace(/\s+([，。；、])/g, "$1")
    .trim();
}

export function stripInternalTrackerIds(text: string): string {
  return tidyPunctuation(
    text
      .replace(TICKET_AND_ADR, "供应商选定")
      .replace(TICKET_ID, "供应商选定工作")
      .replace(ADR_ID, "供应商选定记录")
      .replace(SCRATCH_PATH, "")
      .replace(ADR_FILE_PATH, "")
      .replace(/（见调研笔记）/g, "")
      .replace(/见调研笔记/g, ""),
  );
}

function isInternalPathNote(text: string): boolean {
  return (
    text.includes(".scratch/") ||
    text.includes("docs/adr/") ||
    /^\s*(调研原文|ADR 原文)[：:]/.test(text)
  );
}

function vendorStatusCopy(notice: ConfidentialityNotice): string {
  if (notice.vendor_selected || notice.ticket_02_closed) {
    return "供应商已选定。本页只陈述当前可核对的事实。";
  }
  return "供应商尚未选定。公开条款核验的出筛集合为空，因此不能把任何候选写成已选定供应商。";
}

function processorCopy(notice: ConfidentialityNotice): string {
  if (notice.vendor_selected && notice.selected_vendor !== null) {
    return `当前选定处理方：${notice.selected_vendor}。当前提取引擎为 ${notice.current_extraction_engine}。`;
  }
  if (notice.current_extraction_engine === "vendor") {
    return "处理方尚未选定。系统尚未开通对第三方模型的付费调用。";
  }
  return "处理方尚未选定。当前默认提取引擎是本地假实现，不把零件图发给第三方多模态大模型。";
}

function trainingCopy(notice: ConfidentialityNotice): string {
  if (notice.used_for_training_statement.includes("待填")) {
    return "书面不训练承诺：待填。供应商尚未选定，不得把任何供应商帮助页或口头承诺写成已落实。";
  }
  return stripInternalTrackerIds(notice.used_for_training_statement);
}

function drawingNotesCopy(notes: string): string {
  return stripInternalTrackerIds(notes.replace("不是票 02 对", "不是对"));
}

function caveatCopy(item: string): string | null {
  if (isInternalPathNote(item)) {
    return null;
  }
  if (item.includes("必须来自") && item.includes("待填格子保持待填")) {
    return "三条硬门槛的判定以当前供应商决定为准；待填格子保持待填。";
  }
  const cleaned = stripInternalTrackerIds(item);
  return cleaned === "" ? null : cleaned;
}

export function presentRiskRuleDescription(description: string): string {
  if (/票\s*0*\d+|ADR-\d+|\.scratch/i.test(description)) {
    const main = description.replace(/（[^）]*）/g, "").trim();
    return `${main}（暂定规则，待本厂真实样本核定）`;
  }
  return stripInternalTrackerIds(description);
}

export function presentConfidentialityNotice(notice: ConfidentialityNotice): ConfidentialityNoticeView {
  const caveats = notice.caveats
    .map(caveatCopy)
    .filter((item): item is string => item !== null);

  return {
    vendorSelected: notice.vendor_selected,
    vendorStatus: vendorStatusCopy(notice),
    decisionStatus: stripInternalTrackerIds(notice.adr_status),
    extractionEngine: notice.current_extraction_engine,
    drawingLocation: stripInternalTrackerIds(notice.drawing_storage.location_summary),
    drawingNotes: drawingNotesCopy(notice.drawing_storage.notes),
    processorSummary: processorCopy(notice),
    decisionLine: stripInternalTrackerIds(notice.vendor_decision_line),
    decisionLineNote: notice.selected_vendor ? "已选定" : "未选定",
    hardGates: notice.hard_gates.map((gate) => ({
      ...gate,
      verdict: stripInternalTrackerIds(gate.verdict),
      evidence: stripInternalTrackerIds(gate.evidence),
    })),
    trainingStatement: trainingCopy(notice),
    dpaStatement: stripInternalTrackerIds(notice.dpa_statement),
    implementationConstraints: notice.implementation_constraints.map(stripInternalTrackerIds),
    caveats,
  };
}
