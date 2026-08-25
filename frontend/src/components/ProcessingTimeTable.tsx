import { formatDurationSeconds } from "@/lib/duration";
import type { DrawingProcessingTime } from "@/lib/types";

type ProcessingTimeTableProps = {
  items: DrawingProcessingTime[];
};

export function ProcessingTimeTable({ items }: ProcessingTimeTableProps) {
  return (
    <section aria-labelledby="processing-time-table-heading">
      <h2 id="processing-time-table-heading" className="text-sm font-semibold text-stone-900">
        已复核零件图
      </h2>
      {items.length === 0 ? (
        <p className="mt-3 rounded-xl border border-dashed border-stone-200 bg-white px-4 py-6 text-sm text-stone-500">
          还没有已复核的零件图，因此没有处理耗时可对照。
        </p>
      ) : (
        <div className="mt-3 overflow-x-auto rounded-xl border border-stone-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-stone-200 bg-stone-50 text-xs text-stone-500">
              <tr>
                <th className="px-4 py-2 font-medium">零件图</th>
                <th className="px-4 py-2 font-medium">处理耗时</th>
                <th className="px-4 py-2 font-medium">分级</th>
                <th className="px-4 py-2 font-medium">提取</th>
                <th className="px-4 py-2 font-medium">复核</th>
                <th className="px-4 py-2 font-medium">已复核于</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {items.map((item) => (
                <tr key={item.part_drawing_id}>
                  <td className="max-w-xs truncate px-4 py-2 text-stone-900">{item.original_filename}</td>
                  <td className="px-4 py-2 font-medium text-stone-900">
                    {formatDurationSeconds(item.processing_seconds)}
                  </td>
                  <td className="px-4 py-2 text-stone-700">{formatDurationSeconds(item.grading_seconds)}</td>
                  <td className="px-4 py-2 text-stone-700">
                    {formatDurationSeconds(item.extraction_seconds)}
                  </td>
                  <td className="px-4 py-2 text-stone-700">{formatDurationSeconds(item.review_seconds)}</td>
                  <td className="px-4 py-2 text-stone-500">
                    {new Date(item.reviewed_at).toLocaleString("zh-CN")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
