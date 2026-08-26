import { formatDurationSeconds } from "@/lib/duration";
import type { ProcessingTimeComparison } from "@/lib/types";

type ProcessingTimeSummaryProps = {
  comparison: ProcessingTimeComparison;
};

function savedLabel(savedSeconds: number | null): string {
  if (savedSeconds === null) {
    return "还不能对照";
  }
  if (savedSeconds > 0) {
    return `平均节省 ${formatDurationSeconds(savedSeconds)}`;
  }
  if (savedSeconds < 0) {
    return `平均多用 ${formatDurationSeconds(Math.abs(savedSeconds))}`;
  }
  return "与人工基线持平";
}

export function ProcessingTimeSummary({ comparison }: ProcessingTimeSummaryProps) {
  return (
    <section aria-labelledby="processing-time-summary-heading" className="space-y-4">
      <div>
        <h2 id="processing-time-summary-heading" className="text-sm font-bold text-slate-900">
          本厂效能对照
        </h2>
        <p className="mt-0.5 text-xs text-slate-500">
          自动记录从「图纸上传」到「完成复核」的耗时，与人工录入基线对比提效数据
        </p>
      </div>
      <dl className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="glass-card p-4 backdrop-blur-xl">
          <dt className="text-xs font-medium text-slate-500">平均处理耗时</dt>
          <dd className="mt-1 text-xl font-bold font-mono text-slate-900">
            {formatDurationSeconds(comparison.average_processing_seconds)}
          </dd>
          <p className="mt-1 text-[11px] text-slate-400">计入 {comparison.reviewed_count} 张已复核零件图</p>
        </div>
        <div className="glass-card p-4 backdrop-blur-xl">
          <dt className="text-xs font-medium text-slate-500">人工基线平均</dt>
          <dd className="mt-1 text-xl font-bold font-mono text-slate-900">
            {formatDurationSeconds(comparison.average_baseline_seconds)}
          </dd>
          <p className="mt-1 text-[11px] text-slate-400">已录入 {comparison.baseline_count} 条纯人工基线</p>
        </div>
        <div className="glass-card p-4 backdrop-blur-xl">
          <dt className="text-xs font-medium text-slate-500">效能提升对照</dt>
          <dd className="mt-1 text-xl font-bold font-mono text-emerald-600">
            {savedLabel(comparison.saved_seconds)}
          </dd>
          <p className="mt-1 text-[11px] text-slate-400">
            {comparison.saved_seconds === null
              ? "需至少1张已复核图纸与1条基线"
              : "基线均值 - 工具处理均值"}
          </p>
        </div>
        <div className="glass-card p-4 backdrop-blur-xl">
          <dt className="text-xs font-medium text-slate-500">未计入零件图</dt>
          <dd className="mt-1 text-xl font-bold font-mono text-slate-900">
            {comparison.excluded_unreviewed_count} <span className="text-xs font-normal text-slate-500">张</span>
          </dd>
          <p className="mt-1 text-[11px] text-slate-400">未复核图纸不计入统计</p>
        </div>
      </dl>
      <div className="glass-card-subtle p-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">阶段平均耗时拆解</h3>
        <dl className="mt-3 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl bg-white/60 p-3 shadow-2xs">
            <dt className="text-xs text-slate-500">AI 分级耗时</dt>
            <dd className="text-sm font-bold font-mono text-slate-900">
              {formatDurationSeconds(comparison.average_grading_seconds)}
            </dd>
          </div>
          <div className="rounded-xl bg-white/60 p-3 shadow-2xs">
            <dt className="text-xs text-slate-500">特征提取耗时</dt>
            <dd className="text-sm font-bold font-mono text-slate-900">
              {formatDurationSeconds(comparison.average_extraction_seconds)}
            </dd>
          </div>
          <div className="rounded-xl bg-white/60 p-3 shadow-2xs">
            <dt className="text-xs text-slate-500">人工复核确认耗时</dt>
            <dd className="text-sm font-bold font-mono text-slate-900">
              {formatDurationSeconds(comparison.average_review_seconds)}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}
