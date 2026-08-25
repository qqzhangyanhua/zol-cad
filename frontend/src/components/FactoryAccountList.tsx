"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { parseFactoryAccount, readErrorDetail, type FactoryAccount } from "@/lib/types";

type FactoryAccountListProps = {
  items: FactoryAccount[];
};

export function FactoryAccountList({ items }: FactoryAccountListProps) {
  const router = useRouter();
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function disableAccount(account: FactoryAccount): Promise<void> {
    setPendingId(account.id);
    setError(null);
    const response = await fetch(`/api/admin/accounts/${account.id}/disable`, { method: "POST" });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "无法停用账号");
      setPendingId(null);
      return;
    }
    parseFactoryAccount(payload);
    setPendingId(null);
    router.refresh();
  }

  return (
    <section className="rounded-xl border border-stone-200 bg-white">
      <div className="border-b border-stone-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-stone-900">本厂账号</h2>
        <p className="mt-1 text-xs text-stone-500">停用后该报价员不能再登录。管理员账号不能从这里停用。</p>
      </div>
      {error ? (
        <p className="px-4 pt-3 text-xs text-red-700" role="alert">
          {error}
        </p>
      ) : null}
      <table className="w-full text-left text-sm">
        <thead className="text-xs text-stone-500">
          <tr>
            <th className="px-4 py-2 font-medium">账号</th>
            <th className="px-4 py-2 font-medium">角色</th>
            <th className="px-4 py-2 font-medium">状态</th>
            <th className="px-4 py-2 font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          {items.map((account) => (
            <tr key={account.id} className="border-t border-stone-100">
              <td className="px-4 py-2.5 text-stone-900">{account.username}</td>
              <td className="px-4 py-2.5 text-stone-600">{account.role === "admin" ? "管理员" : "报价员"}</td>
              <td className="px-4 py-2.5 text-stone-600">{account.disabled_at ? "已停用" : "可用"}</td>
              <td className="px-4 py-2.5">
                {account.role === "quoter" && account.disabled_at === null ? (
                  <button
                    type="button"
                    disabled={pendingId === account.id}
                    onClick={() => {
                      void disableAccount(account);
                    }}
                    className="h-8 rounded-md border border-stone-300 px-2.5 text-xs font-medium text-stone-700 hover:bg-stone-100 disabled:opacity-50"
                  >
                    {pendingId === account.id ? "停用中…" : "停用"}
                  </button>
                ) : (
                  <span className="text-xs text-stone-400">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
