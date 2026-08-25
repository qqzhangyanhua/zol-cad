import { formatDurationSeconds } from "@/lib/duration";
import type { ManualBaseline } from "@/lib/types";

type ManualBaselineListProps = {
  items: ManualBaseline[];
};

export function ManualBaselineList({ items }: ManualBaselineListProps) {
  if (items.length === 0) {
    return (
      <p className="mt-3 rounded-xl border border-dashed border-stone-200 bg-white px-4 py-6 text-sm text-stone-500">
        还没有人工基线。试用初期请先对几张纯人工作业计时，再录入对照。
      </p>
    );
  }
  return (
    <ul className="mt-3 divide-y divide-stone-100 overflow-hidden rounded-xl border border-stone-200 bg-white">
      {items.map((item) => (
        <li key={item.id} className="flex items-start justify-between gap-4 px-4 py-3">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-stone-900">{item.part_description}</p>
            <time className="mt-1 block text-xs text-stone-500" dateTime={item.recorded_at}>
              {new Date(item.recorded_at).toLocaleString("zh-CN")}
            </time>
          </div>
          <p className="shrink-0 text-sm font-medium text-stone-800">
            {formatDurationSeconds(item.manual_duration_seconds)}
          </p>
        </li>
      ))}
    </ul>
  );
}
