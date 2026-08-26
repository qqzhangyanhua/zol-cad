import Link from "next/link";
import type { QuoteTaskSummary } from "@/lib/types";

type QuoteTaskListProps = {
  items: QuoteTaskSummary[];
};

export function QuoteTaskList({ items }: QuoteTaskListProps) {
  return (
    <div className="glass-card overflow-hidden backdrop-blur-xl">
      <div className="border-b border-slate-100/80 px-6 py-3.5 bg-white/40">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          任务列表 ({items.length})
        </h3>
      </div>
      <ul className="divide-y divide-slate-100/80">
        {items.map((item) => (
          <li key={item.id} className="transition-colors hover:bg-white/60">
            <Link
              href={`/quote-tasks/${item.id}`}
              className="flex items-center justify-between gap-4 px-6 py-4"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-semibold text-slate-900">{item.name}</span>
                  <span className="rounded-full bg-blue-50 border border-blue-200/60 px-2 py-0.5 text-[11px] font-semibold text-blue-700">
                    {item.review_status}
                  </span>
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span className="font-medium text-slate-700">客户: {item.customer_name}</span>
                  <span className="text-slate-400">·</span>
                  <span>包含 {item.drawing_count} 张零件图</span>
                </div>
              </div>
              <div className="flex items-center gap-4 shrink-0">
                <time className="text-xs text-slate-400 font-mono" dateTime={item.created_at}>
                  {new Date(item.created_at).toLocaleString("zh-CN", {
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </time>
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/80 text-slate-400 shadow-xs border border-white">
                  →
                </span>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
