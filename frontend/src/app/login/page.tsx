import { LoginForm } from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center bg-stone-100 px-4">
      <section className="w-full max-w-md rounded-2xl border border-stone-200 bg-white p-8 shadow-sm">
        <p className="text-center text-sm font-semibold tracking-wide text-stone-500">
          机加工报价辅助
        </p>
        <h1 className="mt-2 text-center text-2xl font-semibold text-stone-900">
          欢迎回来
        </h1>
        <p className="mt-2 mb-8 text-center text-sm text-stone-500">
          请使用报价员账号登录
        </p>
        <LoginForm />
      </section>
    </main>
  );
}
