"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { readErrorDetail } from "@/lib/types";

export function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setPending(true);
    setError(null);
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      const payload: unknown = await response.json().catch(() => null);
      setError(readErrorDetail(payload) ?? "账号或密码不正确");
      setPending(false);
      return;
    }
    router.replace("/part-drawings");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
        账号
        <input
          name="username"
          autoComplete="username"
          placeholder="请输入用户名"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          className="h-10 rounded-xl border border-slate-200/90 bg-white/80 px-3 text-sm font-normal text-slate-900 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-100"
          required
        />
      </label>
      <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
        密码
        <input
          name="password"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="h-10 rounded-xl border border-slate-200/90 bg-white/80 px-3 text-sm font-normal text-slate-900 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-100"
          required
        />
      </label>
      {error ? (
        <p className="rounded-lg bg-red-50 p-2 text-xs font-medium text-red-600" role="alert">
          ⚠ {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={pending}
        className="btn-primary-capsule mt-2 h-10 w-full text-sm font-medium text-white cursor-pointer disabled:opacity-60"
      >
        {pending ? "登录验证中…" : "登 录"}
      </button>
    </form>
  );
}
