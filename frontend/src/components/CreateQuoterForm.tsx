"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { parseFactoryAccount, readErrorDetail } from "@/lib/types";

export function CreateQuoterForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setPending(true);
    setError(null);
    const response = await fetch("/api/admin/accounts", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "无法创建报价员账号");
      setPending(false);
      return;
    }
    parseFactoryAccount(payload);
    setUsername("");
    setPassword("");
    setPending(false);
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="rounded-xl border border-stone-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-stone-900">创建报价员账号</h2>
      <p className="mt-1 text-xs text-stone-500">只能创建本厂报价员，不能在这里再开一个管理员。</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <label className="block text-xs text-stone-600">
          账号
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border border-stone-200 px-2.5 text-sm text-stone-900 outline-none focus:border-stone-400"
          />
        </label>
        <label className="block text-xs text-stone-600">
          初始密码
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border border-stone-200 px-2.5 text-sm text-stone-900 outline-none focus:border-stone-400"
          />
        </label>
      </div>
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
        {pending ? "创建中…" : "创建报价员"}
      </button>
    </form>
  );
}
