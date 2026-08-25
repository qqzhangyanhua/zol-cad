import Link from "next/link";

import type { QuoteTaskReviewStatus, QuoteTaskSearchParams } from "@/lib/types";
import { QUOTE_TASK_REVIEW_STATUSES } from "@/lib/types";

type QuoteTaskSearchFormProps = {
  values: QuoteTaskSearchParams;
};

export function QuoteTaskSearchForm({ values }: QuoteTaskSearchFormProps) {
  return (
    <form method="get" className="rounded-xl border border-stone-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-stone-900">检索历史报价任务</h2>
      <p className="mt-1 text-xs text-stone-500">
        按客户名称、创建时间、以及由零件图复核进度推导出的状态找回过去的任务。
      </p>
      <div className="mt-4 grid gap-4 md:grid-cols-4">
        <label className="flex flex-col gap-2 text-sm font-medium text-stone-800">
          客户名称
          <input
            name="customer_name"
            defaultValue={values.customer_name ?? ""}
            className="h-10 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm font-normal outline-none focus:border-stone-400 focus:bg-white"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm font-medium text-stone-800">
          起始日期
          <input
            type="date"
            name="created_from"
            defaultValue={values.created_from ?? ""}
            className="h-10 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm font-normal outline-none focus:border-stone-400 focus:bg-white"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm font-medium text-stone-800">
          截止日期
          <input
            type="date"
            name="created_to"
            defaultValue={values.created_to ?? ""}
            className="h-10 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm font-normal outline-none focus:border-stone-400 focus:bg-white"
          />
        </label>
        <label className="flex flex-col gap-2 text-sm font-medium text-stone-800">
          状态
          <select
            name="review_status"
            defaultValue={values.review_status ?? ""}
            className="h-10 rounded-lg border border-stone-200 bg-stone-50 px-3 text-sm font-normal outline-none focus:border-stone-400 focus:bg-white"
          >
            <option value="">全部</option>
            {QUOTE_TASK_REVIEW_STATUSES.map((status: QuoteTaskReviewStatus) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="mt-4 flex gap-3">
        <button
          type="submit"
          className="h-10 rounded-lg bg-stone-900 px-4 text-sm font-medium text-white hover:bg-stone-800"
        >
          检索
        </button>
        <Link
          href="/quote-tasks"
          className="inline-flex h-10 items-center rounded-lg px-3 text-sm text-stone-600 hover:bg-stone-100"
        >
          清除
        </Link>
      </div>
    </form>
  );
}
