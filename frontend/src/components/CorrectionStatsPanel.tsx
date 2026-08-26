import type { CorrectionStats } from "@/lib/types";

type CorrectionStatsPanelProps = {
  stats: CorrectionStats;
};

export function CorrectionStatsPanel({ stats }: CorrectionStatsPanelProps) {
  return (
    <section className="space-y-5" aria-labelledby="correction-stats-heading">
      <div>
        <h2 id="correction-stats-heading" className="text-xl font-semibold text-stone-900">
          修正记录统计
        </h2>
        <p className="mt-1 text-sm text-stone-500">按字段类型汇总本厂报价员对提取值的修改频次。</p>
      </div>
      <p className="rounded-lg border border-stone-200 bg-white px-4 py-3 text-sm leading-6 text-stone-600">
        {stats.purpose}
      </p>
      {stats.items.length === 0 ? (
        <p className="text-sm text-stone-500">本厂还没有修正记录。</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full max-w-xl overflow-hidden rounded-lg border border-stone-200 bg-white text-sm">
            <caption className="sr-only">按字段类型聚合的修正频次</caption>
            <thead className="bg-stone-50 text-left text-stone-500">
              <tr>
                <th className="px-4 py-2 font-medium">字段类型</th>
                <th className="px-4 py-2 font-medium">修改次数</th>
              </tr>
            </thead>
            <tbody>
              {stats.items.map((row) => (
                <tr key={row.field_type} className="border-t border-stone-100 text-stone-800">
                  <td className="px-4 py-2">{row.field_type}</td>
                  <td className="px-4 py-2">{row.correction_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
