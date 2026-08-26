import { LogoIcon, ShieldCheckIcon } from "@/components/Icons";
import { LoginForm } from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <main className="glass-shell flex min-h-screen flex-1 items-center justify-center p-4">
      <section className="glass-card relative w-full max-w-md overflow-hidden p-8 shadow-2xl backdrop-blur-2xl">
        <div className="flex flex-col items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600/10 text-blue-600 shadow-xs mb-3">
            <LogoIcon className="h-8 w-8" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">智造报价助手</h1>
          <p className="mt-0.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
            CAD Quote Assistant
          </p>
          <p className="mt-2 mb-6 text-xs text-slate-500">
            精密制造工艺审查与智能报价工作台
          </p>
        </div>

        <LoginForm />

        <div className="mt-8 border-t border-slate-200/60 pt-4 flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
          <ShieldCheckIcon className="h-3.5 w-3.5" />
          <span>2024 © 智造科技 · 企业数据安全隔离保护</span>
        </div>
      </section>
    </main>
  );
}
