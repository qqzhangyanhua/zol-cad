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
    <form onSubmit={onSubmit} className="flex flex-col gap-5">
      <label className="flex flex-col gap-2 text-sm font-medium text-stone-800">
        账号
        <input
          name="username"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          className="h-11 rounded-lg border border-stone-200 bg-stone-50 px-3 text-base font-normal text-stone-900 outline-none focus:border-stone-400 focus:bg-white"
          required
        />
      </label>
      <label className="flex flex-col gap-2 text-sm font-medium text-stone-800">
        密码
        <input
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="h-11 rounded-lg border border-stone-200 bg-stone-50 px-3 text-base font-normal text-stone-900 outline-none focus:border-stone-400 focus:bg-white"
          required
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
        className="h-11 rounded-lg bg-stone-900 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-60"
      >
        {pending ? "登录中…" : "登录"}
      </button>
    </form>
  );
}
