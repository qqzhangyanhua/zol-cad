"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  parseFactoryPreferences,
  readErrorDetail,
  RISK_LABEL_NAMES,
  type RiskLabelName,
} from "@/lib/types";

type RiskLabelPriorityEditorProps = {
  priority: RiskLabelName[];
};

function moveItem(items: RiskLabelName[], index: number, offset: number): RiskLabelName[] {
  const nextIndex = index + offset;
  if (nextIndex < 0 || nextIndex >= items.length) {
    return items;
  }
  const next = [...items];
  const [moved] = next.splice(index, 1);
  next.splice(nextIndex, 0, moved);
  return next;
}

export function RiskLabelPriorityEditor({ priority }: RiskLabelPriorityEditorProps) {
  const router = useRouter();
  const [order, setOrder] = useState<RiskLabelName[]>(
    priority.length === RISK_LABEL_NAMES.length ? priority : [...RISK_LABEL_NAMES],
  );
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function save(next: RiskLabelName[]): Promise<void> {
    setPending(true);
    setError(null);
    const response = await fetch("/api/admin/risk-label-priority", {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ priority: next }),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "无法保存展示优先级");
      setPending(false);
      return;
    }
    const saved = parseFactoryPreferences(payload);
    setOrder(saved.risk_label_priority);
    setPending(false);
    router.refresh();
  }

  return (
    <section className="rounded-xl border border-stone-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-stone-900">风险标签展示优先级</h2>
      <p className="mt-1 text-xs text-stone-500">只改界面排序，不改规则是否触发，也不改阈值。</p>
      <ol className="mt-3 space-y-2">
        {order.map((name, index) => (
          <li
            key={name}
            className="flex items-center justify-between rounded-md border border-stone-200 px-3 py-2 text-sm"
          >
            <span className="text-stone-900">
              {index + 1}. {name}
            </span>
            <span className="flex gap-2">
              <button
                type="button"
                disabled={pending || index === 0}
                onClick={() => {
                  const next = moveItem(order, index, -1);
                  setOrder(next);
                  void save(next);
                }}
                className="h-8 rounded-md border border-stone-300 px-2 text-xs text-stone-700 hover:bg-stone-100 disabled:opacity-40"
              >
                上移
              </button>
              <button
                type="button"
                disabled={pending || index === order.length - 1}
                onClick={() => {
                  const next = moveItem(order, index, 1);
                  setOrder(next);
                  void save(next);
                }}
                className="h-8 rounded-md border border-stone-300 px-2 text-xs text-stone-700 hover:bg-stone-100 disabled:opacity-40"
              >
                下移
              </button>
            </span>
          </li>
        ))}
      </ol>
      {error ? (
        <p className="mt-2 text-xs text-red-700" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
