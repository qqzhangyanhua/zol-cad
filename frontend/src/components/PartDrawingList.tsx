import Link from "next/link";
import { ExperimentalMark } from "@/components/ExperimentalMark";
import { LowQualityMark } from "@/components/LowQualityMark";
import { PartDrawingStatusBadge } from "@/components/PartDrawingStatusBadge";
import { QualityGradeBadge } from "@/components/QualityGradeBadge";
import { partDrawingListRowAccent, partDrawingStatusTone } from "@/lib/partDrawingStatusPresentation";
import type { PartDrawing } from "@/lib/types";

type PartDrawingListProps = {
  items: PartDrawing[];
  quoteTaskNames?: Record<string, string>;
};

export function PartDrawingList({ items, quoteTaskNames = {} }: PartDrawingListProps) {
  return (
    <div className="glass-card overflow-hidden backdrop-blur-xl">
      <div className="border-b border-slate-100 px-6 py-3.5 bg-white/40">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">图纸列表 ({items.length})</h3>
      </div>
      <ul className="divide-y divide-slate-100/80">
        {items.map((item) => (
          <li
            key={item.id}
            className={`transition-colors hover:bg-white/60 ${partDrawingListRowAccent(partDrawingStatusTone(item.status))}`}
          >
            <Link
              href={`/part-drawings/${item.id}`}
              className="flex items-center justify-between gap-4 px-6 py-4"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-semibold text-slate-900">
                    {item.original_filename}
                  </span>
                  <QualityGradeBadge grade={item.quality_grade} />
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <PartDrawingStatusBadge status={item.status} />
                  <span className="text-slate-400">·</span>
                  <span>
                    {item.quote_task_id
                      ? `所属任务: ${quoteTaskNames[item.quote_task_id] ?? "报价任务"}`
                      : "未归集任务"}
                  </span>
                  {item.content_type === "application/pdf" ? (
                    <>
                      <span className="text-slate-400">·</span>
                      <span>
                        第 {item.selected_page} 页 / 共 {item.page_count} 页
                      </span>
                    </>
                  ) : null}
                </div>
                {item.experimental_mark || item.low_quality_mark ? (
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    {item.experimental_mark ? <ExperimentalMark text={item.experimental_mark} /> : null}
                    {item.low_quality_mark ? <LowQualityMark text={item.low_quality_mark} /> : null}
                  </div>
                ) : null}
              </div>
              <div className="flex items-center gap-4 shrink-0">
                <time className="text-xs text-slate-400 font-mono" dateTime={item.uploaded_at}>
                  {new Date(item.uploaded_at).toLocaleString("zh-CN", {
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
