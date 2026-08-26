"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { parseQuoteTaskDetail, readErrorDetail } from "@/lib/types";

export function QuoteTaskCreateForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setPending(true);
    setError(null);
    const response = await fetch("/api/quote-tasks", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name, customer_name: customerName }),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "创建报价任务失败");
      setPending(false);
      return;
    }
    const created = parseQuoteTaskDetail(payload);
    router.push(`/quote-tasks/${created.id}`);
    router.refresh();
  }

  return (
    <form
      onSubmit={(event) => {
        void onSubmit(event);
      }}
      className="glass-card p-5 backdrop-blur-xl"
    >
      <div className="flex items-center justify-between pb-3 border-b border-slate-100/80">
        <div>
          <h2 className="text-sm font-bold text-slate-900">新建报价任务</h2>
          <p className="mt-0.5 text-xs text-slate-500">归集客户本次询价的零件图清单</p>
        </div>
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
          任务名称
          <input
            name="name"
            value={name}
            placeholder="例如：精密阀门组试制报价-2405"
            onChange={(event) => setName(event.target.value)}
            className="h-9 w-full rounded-xl border border-slate-200 bg-white/70 px-3 text-xs font-normal text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100"
            required
          />
        </label>
        <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
          客户名称
          <input
            name="customer_name"
            value={customerName}
            placeholder="例如：苏州精密装备有限公司"
            onChange={(event) => setCustomerName(event.target.value)}
            className="h-9 w-full rounded-xl border border-slate-200 bg-white/70 px-3 text-xs font-normal text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100"
            required
          />
        </label>
      </div>
      {error ? (
        <p className="mt-3 text-xs text-red-600" role="alert">
          ⚠ {error}
        </p>
      ) : null}
      <div className="mt-4 flex justify-end">
        <button
          type="submit"
          disabled={pending}
          className="btn-primary-capsule h-9 px-5 text-xs text-white cursor-pointer disabled:opacity-60"
        >
          {pending ? "创建中…" : "+ 创建报价任务"}
        </button>
      </div>
    </form>
  );
}
