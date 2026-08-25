"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { minutesToSeconds } from "@/lib/duration";
import { parseManualBaselineResponse, readErrorDetail } from "@/lib/types";

export function ManualBaselineForm() {
  const router = useRouter();
  const [partDescription, setPartDescription] = useState("");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const minutes = Number(durationMinutes);
    if (!Number.isFinite(minutes) || minutes <= 0) {
      setError("请填写大于 0 的人工耗时（分钟）");
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch("/api/manual-baselines", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        part_description: partDescription,
        manual_duration_seconds: minutesToSeconds(minutes),
      }),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "无法录入人工基线");
      setPending(false);
      return;
    }
    parseManualBaselineResponse(payload);
    setPartDescription("");
    setDurationMinutes("");
    router.refresh();
    setPending(false);
  }

  return (
    <form onSubmit={onSubmit} className="mt-3 space-y-3 rounded-xl border border-stone-200 bg-white px-4 py-4">
      <label className="flex flex-col gap-1 text-sm font-medium text-stone-800">
        零件描述
        <input
          name="part_description"
          value={partDescription}
          onChange={(event) => setPartDescription(event.target.value)}
          maxLength={200}
          required
          placeholder="例如：φ40 回转轴，纯人工抄写标题栏与关键尺寸"
          className="h-10 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm font-normal text-stone-900 outline-none focus:border-stone-400 focus:bg-white"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm font-medium text-stone-800">
        人工耗时（分钟）
        <input
          name="manual_duration_minutes"
          type="number"
          min={0.5}
          step={0.5}
          value={durationMinutes}
          onChange={(event) => setDurationMinutes(event.target.value)}
          required
          placeholder="例如：20"
          className="h-10 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm font-normal text-stone-900 outline-none focus:border-stone-400 focus:bg-white"
        />
      </label>
      {error ? (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={pending}
        className="h-10 rounded-lg bg-stone-900 px-4 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-60"
      >
        {pending ? "录入中…" : "录入人工基线"}
      </button>
    </form>
  );
}
