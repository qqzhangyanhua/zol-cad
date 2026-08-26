import { sortRiskLabels, type RiskLabel, type RiskLabelName } from "@/lib/types";
import { AlertTriangleIcon } from "@/components/Icons";

type RiskLabelListProps = {
  labels: RiskLabel[];
  emptyMessage: string;
  priority: readonly RiskLabelName[];
};

function RiskLabelCard({ label }: { label: RiskLabel }) {
  return (
    <details className="group glass-warning-pill overflow-hidden transition-all">
      <summary className="cursor-pointer list-none px-3.5 py-2.5 marker:content-none select-none">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertTriangleIcon className="h-4 w-4 text-amber-600 shrink-0" />
            <span className="font-bold text-amber-950 text-xs">{label.name}</span>
          </div>
          <span className="text-[11px] font-medium text-amber-800/80 group-open:hidden">规则详情 ▾</span>
          <span className="hidden text-[11px] font-medium text-amber-800/80 group-open:inline">收起 ▴</span>
        </div>
      </summary>
      <dl className="space-y-2 border-t border-amber-200/50 bg-amber-50/40 px-3.5 py-2.5 text-xs">
        <div className="grid grid-cols-[4.5rem_minmax(0,1fr)] gap-2">
          <dt className="text-amber-800/70">规则ID</dt>
          <dd className="font-mono text-amber-950 font-semibold">{label.rule_id}</dd>
        </div>
        <div className="grid grid-cols-[4.5rem_minmax(0,1fr)] gap-2">
          <dt className="text-amber-800/70">触发特征值</dt>
          <dd className="text-amber-950 font-semibold">{label.triggering_value}</dd>
        </div>
        <div className="grid grid-cols-[4.5rem_minmax(0,1fr)] gap-2">
          <dt className="text-amber-800/70">判定依据</dt>
          <dd className="leading-relaxed text-amber-900">{label.reason}</dd>
        </div>
      </dl>
    </details>
  );
}

export function RiskLabelList({ labels, emptyMessage, priority }: RiskLabelListProps) {
  const ordered = sortRiskLabels(labels, priority);
  return (
    <section aria-labelledby="risk-label-heading" className="mb-5">
      <div className="mb-2.5 flex items-center justify-between">
        <h3 id="risk-label-heading" className="text-xs font-bold uppercase tracking-wider text-slate-500">
          制造风险特征 ({labels.length})
        </h3>
      </div>
      {labels.length === 0 ? (
        <p role="status" className="glass-card-subtle p-3 text-xs leading-relaxed text-slate-600">
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
