import Link from "next/link";

import type { QuoteTaskSummary } from "@/lib/types";

type QuoteTaskListProps = {
  items: QuoteTaskSummary[];
};

export function QuoteTaskList({ items }: QuoteTaskListProps) {
  return (
    <ul className="divide-y divide-stone-200 overflow-hidden rounded-xl border border-stone-200 bg-white">
      {items.map((item) => (
        <li key={item.id}>
          <Link href={`/quote-tasks/${item.id}`} className="flex items-center justify-between gap-4 px-4 py-4 hover:bg-stone-50">
            <span className="min-w-0">
              <span className="block truncate text-sm font-medium text-stone-900">{item.name}</span>
              <span className="mt-1 flex flex-wrap items-center gap-2 text-xs text-stone-500">
                <span>客户 {item.customer_name}</span>
                <span>{item.review_status}</span>
                <span>{item.drawing_count} 张零件图</span>
              </span>
            </span>
            <time className="shrink-0 text-xs text-stone-500" dateTime={item.created_at}>
              {new Date(item.created_at).toLocaleString("zh-CN")}
            </time>
          </Link>
        </li>
      ))}
    </ul>
  );
}
