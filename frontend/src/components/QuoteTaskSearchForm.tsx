import Link from "next/link";
import type { QuoteTaskReviewStatus, QuoteTaskSearchParams } from "@/lib/types";
import { QUOTE_TASK_REVIEW_STATUSES } from "@/lib/types";

type QuoteTaskSearchFormProps = {
  values: QuoteTaskSearchParams;
};

export function QuoteTaskSearchForm({ values }: QuoteTaskSearchFormProps) {
  return (
    <form method="get" className="glass-card p-5 backdrop-blur-xl">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100/80">
        <div>
          <h2 className="text-sm font-bold text-slate-900">检索历史报价任务</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            按客户名称、创建日期及复核进度快速筛选历史报价任务
          </p>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
          客户名称
          <input
            name="customer_name"
            placeholder="输入客户名..."
            defaultValue={values.customer_name ?? ""}
            className="h-8.5 rounded-xl border border-slate-200 bg-white/70 px-3 text-xs font-normal outline-none transition focus:border-blue-400 focus:bg-white"
          />
        </label>
        <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
          起始日期
          <input
            type="date"
            name="created_from"
            defaultValue={values.created_from ?? ""}
            className="h-8.5 rounded-xl border border-slate-200 bg-white/70 px-3 text-xs font-normal outline-none transition focus:border-blue-400 focus:bg-white"
          />
        </label>
        <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
          截止日期
          <input
            type="date"
            name="created_to"
            defaultValue={values.created_to ?? ""}
            className="h-8.5 rounded-xl border border-slate-200 bg-white/70 px-3 text-xs font-normal outline-none transition focus:border-blue-400 focus:bg-white"
          />
        </label>
        <label className="flex flex-col gap-1.5 text-xs font-semibold text-slate-700">
          复核状态
          <select
            name="review_status"
            defaultValue={values.review_status ?? ""}
            className="h-8.5 rounded-xl border border-slate-200 bg-white/70 px-3 text-xs font-normal outline-none transition focus:border-blue-400 focus:bg-white"
          >
            <option value="">全部状态</option>
            {QUOTE_TASK_REVIEW_STATUSES.map((status: QuoteTaskReviewStatus) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="mt-4 flex items-center justify-end gap-2.5">
        <Link
          href="/quote-tasks"
          className="btn-secondary-capsule h-8 px-4 text-xs text-slate-600 cursor-pointer"
        >
          重置
        </Link>
        <button
          type="submit"
          className="btn-primary-capsule h-8 px-4 text-xs text-white cursor-pointer"
        >
          查询任务
        </button>
      </div>
    </form>
  );
}
