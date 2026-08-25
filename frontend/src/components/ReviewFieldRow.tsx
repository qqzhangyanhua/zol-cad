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
      className={`rounded-lg border px-3 py-2.5 ${
        field.ignored ? "border-stone-200 bg-stone-50" : "border-stone-200 bg-white"
      }`}
    >
      <div className="grid grid-cols-[7rem_minmax(0,1fr)] items-start gap-3">
        <div className="pt-0.5">
          <p className="text-xs font-medium text-stone-800">{field.label}</p>
          <p className="mt-0.5 text-[11px] text-stone-400">{field.category}</p>
          {needsConfirm ? (
            <p className="mt-1 text-[11px] font-medium text-amber-700">需确认</p>
          ) : null}
          {field.confirmed && !field.ignored ? (
            <p className="mt-1 text-[11px] font-medium text-emerald-700">已确认</p>
          ) : null}
          {field.ignored ? (
            <p className="mt-1 text-[11px] font-medium text-stone-500">已忽略</p>
          ) : null}
          {field.source === "added" ? (
            <p className="mt-1 text-[11px] font-medium text-sky-700">补录</p>
          ) : null}
        </div>
        <div>
          {readOnly ? (
            <p className="min-h-8 rounded-md bg-stone-50 px-2.5 py-1.5 text-sm text-stone-900">
              {field.value === null || field.value === "" ? (
                <span className="text-stone-400">（空）</span>
              ) : (
                field.value
              )}
            </p>
          ) : (
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
              className={`h-9 w-full rounded-md border px-2.5 text-sm text-stone-900 outline-none focus:border-stone-400 ${
                showEmpty ? "border-stone-200 bg-stone-50 placeholder:text-stone-400" : "border-stone-200 bg-white"
              }`}
            />
            {field.key === "material" && materialCandidates.length > 0 ? (
              <datalist id="material-candidates">
                {materialCandidates.map((name) => (
                  <option key={name} value={name} />
                ))}
              </datalist>
            ) : null}
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {!readOnly && needsConfirm ? (
              <button
                type="button"
                disabled={pending}
                onClick={() => {
                  void confirmField();
                }}
                className="h-8 rounded-md bg-stone-900 px-2.5 text-xs font-medium text-white hover:bg-stone-800 disabled:opacity-50"
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
                className="h-8 rounded-md border border-stone-300 px-2.5 text-xs font-medium text-stone-700 hover:bg-stone-100 disabled:opacity-50"
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
                className="h-8 rounded-md border border-stone-300 px-2.5 text-xs font-medium text-stone-700 hover:bg-stone-100 disabled:opacity-50"
              >
                撤销忽略
              </button>
            ) : null}
            {saved && !readOnly ? <span className="text-[11px] text-stone-500">已保存</span> : null}
          </div>
          {error ? (
            <p className="mt-1 text-xs text-red-700" role="alert">
              {error}
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
