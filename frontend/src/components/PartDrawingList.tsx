import Link from "next/link";

import { ExperimentalMark } from "@/components/ExperimentalMark";
import { LowQualityMark } from "@/components/LowQualityMark";
import { QualityGradeBadge } from "@/components/QualityGradeBadge";
import type { PartDrawing } from "@/lib/types";

type PartDrawingListProps = {
  items: PartDrawing[];
};

export function PartDrawingList({ items }: PartDrawingListProps) {
  return (
    <ul className="divide-y divide-stone-200 border-t border-stone-200">
      {items.map((item) => (
        <li key={item.id}>
          <Link
            href={`/part-drawings/${item.id}`}
            className="flex items-center justify-between gap-4 px-6 py-4 hover:bg-white"
          >
            <span className="min-w-0">
              <span className="block truncate text-sm font-medium text-stone-900">
                {item.original_filename}
              </span>
              <span className="mt-1 flex flex-wrap items-center gap-2">
                <QualityGradeBadge grade={item.quality_grade} />
                <span className="text-xs text-stone-500">{item.status}</span>
                {item.content_type === "application/pdf" ? (
                  <span className="text-xs text-stone-500">
                    指定第 {item.selected_page} 页（共 {item.page_count} 页）
                  </span>
                ) : null}
              </span>
              {item.experimental_mark || item.low_quality_mark ? (
                <span className="mt-2 flex flex-wrap items-center gap-2">
                  {item.experimental_mark ? <ExperimentalMark text={item.experimental_mark} /> : null}
                  {item.low_quality_mark ? <LowQualityMark text={item.low_quality_mark} /> : null}
                </span>
              ) : null}
            </span>
            <time className="shrink-0 text-xs text-stone-500" dateTime={item.uploaded_at}>
              {new Date(item.uploaded_at).toLocaleString("zh-CN")}
            </time>
          </Link>
        </li>
      ))}
    </ul>
  );
}
