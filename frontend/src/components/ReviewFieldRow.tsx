"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { parsePartDrawing, readErrorDetail, type ExtractedField } from "@/lib/types";

type ReviewFieldRowProps = {
  drawingId: string;
  field: ExtractedField;
  readOnly: boolean;
  materialCandidates: string[];
};

function displayValue(value: string | null): string {
  return value ?? "";
}

export function ReviewFieldRow({
  drawingId,
  field,
  readOnly,
  materialCandidates,
}: ReviewFieldRowProps) {
  const router = useRouter();
  const [draft, setDraft] = useState(displayValue(field.value));
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const saveTimer = useRef<number | null>(null);

  async function persistValue(next: string): Promise<boolean> {
    setPending(true);
    setError(null);
    const response = await fetch(`/api/part-drawings/${drawingId}/fields/${field.key}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ value: next === "" ? null : next }),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "保存失败");
      setPending(false);
      return false;
    }
    parsePartDrawing(payload);
    setSaved(true);
    setPending(false);
    router.refresh();
    return true;
  }

  function scheduleSave(next: string): void {
    if (saveTimer.current !== null) {
      window.clearTimeout(saveTimer.current);
    }
    saveTimer.current = window.setTimeout(() => {
      if (next !== displayValue(field.value)) {
        void persistValue(next);
      }
    }, 400);
  }

  async function confirmField(): Promise<void> {
    if (pending) {
      return;
    }
    if (saveTimer.current !== null) {
      window.clearTimeout(saveTimer.current);
      saveTimer.current = null;
    }
    if (draft !== displayValue(field.value)) {
      await persistValue(draft);
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch(
      `/api/part-drawings/${drawingId}/fields/${field.key}/confirm`,
      { method: "POST" },
    );
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "确认失败");
      setPending(false);
      return;
    }
    parsePartDrawing(payload);
    setPending(false);
    router.refresh();
  }

  async function toggleIgnore(nextIgnored: boolean): Promise<void> {
    if (pending) {
      return;
    }
    setPending(true);
    setError(null);
    const action = nextIgnored ? "ignore" : "unignore";
    const response = await fetch(`/api/part-drawings/${drawingId}/fields/${field.key}/${action}`, {
      method: "POST",
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? (nextIgnored ? "忽略失败" : "撤销忽略失败"));
      setPending(false);
      return;
    }
    parsePartDrawing(payload);
    setPending(false);
    router.refresh();
  }

  const needsConfirm = field.requires_confirmation && !field.confirmed && !field.ignored;
  const showEmpty = draft === "";

  return (
    <div
      className={`rounded-xl border p-3 transition-all ${
        field.ignored
          ? "border-slate-200/60 bg-slate-50/50 opacity-70"
          : "border-slate-200/80 bg-white/80 shadow-2xs"
      }`}
    >
      <div className="grid grid-cols-[6.5rem_minmax(0,1fr)] items-start gap-3">
        <div className="pt-0.5">
          <p className="text-xs font-semibold text-slate-800">{field.label}</p>
          <p className="mt-0.5 text-[10px] text-slate-400">{field.category}</p>
          {needsConfirm ? (
            <span className="mt-1 inline-block rounded-md bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700 border border-amber-200/60">
              需确认
            </span>
          ) : null}
          {field.confirmed && !field.ignored ? (
            <span className="mt-1 inline-block rounded-md bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200/60">
              ✓ 已确认
            </span>
          ) : null}
          {field.ignored ? (
            <span className="mt-1 inline-block rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
              已忽略
            </span>
          ) : null}
          {field.source === "added" ? (
            <span className="mt-1 inline-block rounded-md bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700 border border-blue-200/60">
              补录
            </span>
          ) : null}
        </div>
        <div>
          {readOnly ? (
            <div className="min-h-8 rounded-lg bg-slate-50/80 px-2.5 py-1.5 text-xs text-slate-900 font-medium">
              {field.value === null || field.value === "" ? (
                <span className="text-slate-400">（空）</span>
              ) : (
                field.value
              )}
            </div>
          ) : (
            <>
              <input
                aria-label={field.label}
                value={draft}
                placeholder="（空）"
                list={field.key === "material" && materialCandidates.length > 0 ? "material-candidates" : undefined}
                onChange={(event) => {
                  const next = event.target.value;
                  setSaved(false);
                  setDraft(next);
                  scheduleSave(next);
                }}
                onBlur={() => {
                  if (draft !== displayValue(field.value)) {
                    void persistValue(draft);
                  }
                }}
                className={`h-8.5 w-full rounded-lg border px-2.5 text-xs font-medium text-slate-900 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100 ${
                  showEmpty
                    ? "border-slate-200 bg-slate-50/60 placeholder:text-slate-400"
                    : "border-slate-200 bg-white"
                }`}
              />
              {field.key === "material" && materialCandidates.length > 0 ? (
                <datalist id="material-candidates">
                  {materialCandidates.map((name) => (
                    <option key={name} value={name} />
                  ))}
                </datalist>
              ) : null}
            </>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {!readOnly && needsConfirm ? (
              <button
                type="button"
                disabled={pending}
                onClick={() => {
                  void confirmField();
                }}
                className="btn-primary-capsule h-7 px-3 text-[11px] text-white cursor-pointer disabled:opacity-50"
              >
                {pending ? "处理中…" : "确认"}
              </button>
            ) : null}
            {!readOnly && !field.ignored ? (
              <button
                type="button"
                disabled={pending}
                onClick={() => {
                  void toggleIgnore(true);
                }}
                className="btn-secondary-capsule h-7 px-2.5 text-[11px] text-slate-600 cursor-pointer disabled:opacity-50"
              >
                忽略
              </button>
            ) : null}
            {!readOnly && field.ignored ? (
              <button
                type="button"
                disabled={pending}
                onClick={() => {
                  void toggleIgnore(false);
                }}
                className="btn-secondary-capsule h-7 px-2.5 text-[11px] text-slate-600 cursor-pointer disabled:opacity-50"
              >
                撤销忽略
              </button>
            ) : null}
            {saved && !readOnly ? (
              <span className="text-[11px] font-medium text-emerald-600">✓ 已保存</span>
            ) : null}
          </div>
          {error ? (
            <p className="mt-1 text-xs text-red-600" role="alert">
              ⚠ {error}
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
