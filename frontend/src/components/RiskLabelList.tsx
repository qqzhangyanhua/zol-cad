import { sortRiskLabels, type RiskLabel, type RiskLabelName } from "@/lib/types";

type RiskLabelListProps = {
  labels: RiskLabel[];
  emptyMessage: string;
  priority: readonly RiskLabelName[];
};

function RiskLabelCard({ label }: { label: RiskLabel }) {
  return (
    <details className="group rounded-lg border border-amber-200 bg-amber-50 open:bg-amber-50">
      <summary className="cursor-pointer list-none px-3 py-2.5 marker:content-none">
        <span className="flex items-center justify-between gap-3">
          <span className="inline-flex rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-950">
            {label.name}
          </span>
          <span className="text-[11px] text-amber-800 group-open:hidden">展开看规则与触发值</span>
          <span className="hidden text-[11px] text-amber-800 group-open:inline">收起</span>
        </span>
      </summary>
      <dl className="space-y-2 border-t border-amber-200 px-3 py-2.5 text-xs">
        <div className="grid grid-cols-[4.5rem_minmax(0,1fr)] gap-2">
          <dt className="text-stone-500">规则</dt>
          <dd className="font-mono text-stone-800">{label.rule_id}</dd>
        </div>
        <div className="grid grid-cols-[4.5rem_minmax(0,1fr)] gap-2">
          <dt className="text-stone-500">触发值</dt>
          <dd className="text-stone-900">{label.triggering_value}</dd>
        </div>
        <div className="grid grid-cols-[4.5rem_minmax(0,1fr)] gap-2">
          <dt className="text-stone-500">理由</dt>
          <dd className="leading-5 text-stone-800">{label.reason}</dd>
        </div>
      </dl>
    </details>
  );
}

export function RiskLabelList({ labels, emptyMessage, priority }: RiskLabelListProps) {
  const ordered = sortRiskLabels(labels, priority);
  return (
    <section aria-labelledby="risk-label-heading" className="mb-6">
      <div className="mb-3">
        <h2 id="risk-label-heading" className="text-sm font-semibold text-stone-900">
          风险标签
        </h2>
        <p className="mt-0.5 text-xs text-stone-500">疑似风险，请复核。门槛为暂定值，不是样本调研结论。</p>
      </div>
      {labels.length === 0 ? (
        <p role="note" className="rounded-lg border border-stone-200 bg-white px-3 py-2.5 text-sm leading-6 text-stone-700">
          {emptyMessage}
        </p>
      ) : (
        <ul className="space-y-2">
          {ordered.map((label) => (
            <li key={label.rule_id}>
              <RiskLabelCard label={label} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
