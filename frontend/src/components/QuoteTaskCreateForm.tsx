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
      className="rounded-xl border border-stone-200 bg-white p-4"
    >
      <h2 className="text-sm font-semibold text-stone-900">新建报价任务</h2>
      <p className="mt-1 text-xs text-stone-500">只填任务名称和客户名称，用来归集零件图。不含金额，也不走审批。</p>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-2 text-sm font-medium text-stone-800">
          任务名称
          <input
            name="name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="h-10 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm font-normal text-stone-900 outline-none focus:border-stone-400 focus:bg-white"
            required
          />
        </label>
        <label className="flex flex-col gap-2 text-sm font-medium text-stone-800">
          客户名称
          <input
            name="customer_name"
            value={customerName}
            onChange={(event) => setCustomerName(event.target.value)}
            className="h-10 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm font-normal text-stone-900 outline-none focus:border-stone-400 focus:bg-white"
            required
          />
        </label>
      </div>
      {error ? (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={pending}
        className="mt-4 h-10 rounded-lg bg-stone-900 px-4 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-60"
      >
        {pending ? "创建中…" : "创建报价任务"}
      </button>
    </form>
  );
}
