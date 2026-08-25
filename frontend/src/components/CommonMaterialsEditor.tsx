"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { parseFactoryPreferences, readErrorDetail } from "@/lib/types";

type CommonMaterialsEditorProps = {
  materials: string[];
};

export function CommonMaterialsEditor({ materials }: CommonMaterialsEditorProps) {
  const router = useRouter();
  const [draft, setDraft] = useState(materials.join("\n"));
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const next = draft
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);
    setPending(true);
    setError(null);
    const response = await fetch("/api/admin/common-materials", {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ materials: next }),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "无法保存常用材料");
      setPending(false);
      return;
    }
    const saved = parseFactoryPreferences(payload);
    setDraft(saved.common_materials.join("\n"));
    setPending(false);
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="rounded-xl border border-stone-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-stone-900">本厂常用材料</h2>
      <p className="mt-1 text-xs text-stone-500">
        每行一项。复核时材料字段会把这份列表当作候选，仍允许手输列表外的材料。
      </p>
      <textarea
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        rows={6}
        className="mt-3 w-full rounded-md border border-stone-200 px-2.5 py-2 text-sm text-stone-900 outline-none focus:border-stone-400"
      />
      {error ? (
        <p className="mt-2 text-xs text-red-700" role="alert">
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={pending}
        className="mt-3 h-10 rounded-md bg-stone-900 px-4 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-50"
      >
        {pending ? "保存中…" : "保存常用材料"}
      </button>
    </form>
  );
}
