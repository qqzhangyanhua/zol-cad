"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import {
  parseTenantDeleteChallenge,
  readErrorDetail,
  type TenantDeleteChallenge,
} from "@/lib/types";

type TenantDataDeletePanelProps = {
  factoryName: string;
};

export function TenantDataDeletePanel({ factoryName }: TenantDataDeletePanelProps) {
  const router = useRouter();
  const [challenge, setChallenge] = useState<TenantDeleteChallenge | null>(null);
  const [phrase, setPhrase] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function startDelete(): Promise<void> {
    setPending(true);
    setError(null);
    const response = await fetch("/api/admin/tenant-data/delete-challenge", { method: "POST" });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "无法发起删除确认");
      setPending(false);
      return;
    }
    setChallenge(parseTenantDeleteChallenge(payload));
    setPhrase("");
    setPending(false);
  }

  async function confirmDelete(): Promise<void> {
    if (challenge === null) {
      return;
    }
    setPending(true);
    setError(null);
    const response = await fetch("/api/admin/tenant-data/delete", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        confirm_token: challenge.confirm_token,
        confirm_phrase: phrase,
      }),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setError(readErrorDetail(payload) ?? "删除本厂数据失败");
      setPending(false);
      return;
    }
    router.push("/part-drawings");
    router.refresh();
  }

  return (
    <section className="rounded-xl border border-red-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-red-800">删除本厂全部数据</h2>
      <p className="mt-1 text-xs leading-5 text-stone-500">
        合作终止时清除本厂零件图、提取与复核结果、风险标签、报价任务、修正记录，以及对象存储里的原图。账号还在，再登录时看不到业务残留。此操作不可撤销。
      </p>
      {challenge === null ? (
        <button
          type="button"
          disabled={pending}
          onClick={() => {
            void startDelete();
          }}
          className="mt-4 h-10 rounded-lg border border-red-300 px-4 text-sm font-medium text-red-800 hover:bg-red-50 disabled:opacity-60"
        >
          {pending ? "正在发起确认…" : "发起删除"}
        </button>
      ) : (
        <form
          className="mt-4 space-y-3"
          onSubmit={(event) => {
            event.preventDefault();
            void confirmDelete();
          }}
        >
          <p className="text-xs leading-5 text-stone-600">
            请原样输入下面的确认短语。服务端会核对一次性确认令牌和短语，浏览器弹窗不算数。
          </p>
          <p className="rounded-lg bg-stone-50 px-3 py-2 font-mono text-sm text-stone-800">
            {challenge.confirm_phrase}
          </p>
          <label className="block text-xs text-stone-500">
            确认短语
            <input
              value={phrase}
              onChange={(event) => {
                setPhrase(event.target.value);
              }}
              placeholder={`删除${factoryName}的全部数据`}
              className="mt-1 h-10 w-full rounded-lg border border-stone-300 px-3 text-sm text-stone-900"
            />
          </label>
          <button
            type="submit"
            disabled={pending || phrase.trim() === ""}
            className="h-10 rounded-lg bg-red-700 px-4 text-sm font-medium text-white hover:bg-red-800 disabled:opacity-60"
          >
            {pending ? "正在删除…" : "确认删除本厂全部数据"}
          </button>
        </form>
      )}
      {error ? (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}
