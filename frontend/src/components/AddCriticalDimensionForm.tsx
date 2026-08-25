"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  CRITICAL_DIMENSION_KINDS,
  parsePartDrawing,
  readErrorDetail,
  type CriticalDimensionKind,
} from "@/lib/types";

type AddCriticalDimensionFormProps = {
  drawingId: string;
};

export function AddCriticalDimensionForm({ drawingId }: AddCriticalDimensionFormProps) {
  const router = useRouter();
  const [kind, setKind] = useState<CriticalDimensionKind>("deepest_hole");
  const [value, setValue] = useState("");
  const [label, setLabel] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(): Promise<void> {
    if (pending || value.trim() === "") {
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch(`/api/part-drawings/${drawingId}/fields`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        kind,
        value: value.trim(),
        label: label.trim() === "" ? null : label.trim(),
      }),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "补录失败");
      setPending(false);
      return;
    }
    parsePartDrawing(payload);
    setValue("");
    setLabel("");
    setPending(false);
    router.refresh();
  }

  return (
    <div className="rounded-lg border border-dashed border-stone-300 bg-white px-3 py-3">
      <p className="text-sm font-medium text-stone-900">补录关键尺寸</p>
      <p className="mt-0.5 text-xs text-stone-500">
        AI 完全没提出来的项可以在这里补进结果，并参与风险标签计算。
      </p>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        <label className="text-xs text-stone-600">
          类型
          <select
            value={kind}
            onChange={(event) => {
              setKind(event.target.value as CriticalDimensionKind);
            }}
            className="mt-1 h-9 w-full rounded-md border border-stone-200 bg-white px-2 text-sm text-stone-900"
          >
            {CRITICAL_DIMENSION_KINDS.map((item) => (
              <option key={item.kind} value={item.kind}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-stone-600">
          数值
          <input
            value={value}
            onChange={(event) => {
              setValue(event.target.value);
            }}
            placeholder="例如 Ø8×48 或 IT6"
            className="mt-1 h-9 w-full rounded-md border border-stone-200 px-2.5 text-sm text-stone-900 outline-none focus:border-stone-400"
          />
        </label>
      </div>
      <label className="mt-2 block text-xs text-stone-600">
        名称（可选，槽位已有值时用作补录行标题）
        <input
          value={label}
          onChange={(event) => {
            setLabel(event.target.value);
          }}
          placeholder="另一处深孔"
          className="mt-1 h-9 w-full rounded-md border border-stone-200 px-2.5 text-sm text-stone-900 outline-none focus:border-stone-400"
        />
      </label>
      <button
        type="button"
        disabled={pending || value.trim() === ""}
        onClick={() => {
          void onSubmit();
        }}
        className="mt-3 h-9 rounded-lg bg-stone-900 px-3 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-50"
      >
        {pending ? "正在补录…" : "补录到结果"}
      </button>
      {error ? (
        <p className="mt-2 text-xs text-red-700" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
