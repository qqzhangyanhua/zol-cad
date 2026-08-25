import Link from "next/link";

export default function QuoteTaskNotFound() {
  return (
    <div className="flex min-h-full flex-1 flex-col items-center justify-center bg-stone-50 px-6">
      <p className="text-sm font-medium text-stone-800">报价任务不存在</p>
      <Link href="/quote-tasks" className="mt-6 text-sm text-stone-800 underline">
        返回报价任务
      </Link>
    </div>
  );
}
