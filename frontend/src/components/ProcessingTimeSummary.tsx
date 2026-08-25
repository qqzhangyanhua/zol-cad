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
    <section aria-labelledby="processing-time-summary-heading">
      <h2 id="processing-time-summary-heading" className="text-sm font-semibold text-stone-900">
        本厂对照
      </h2>
      <p className="mt-1 text-xs text-stone-500">
        处理耗时从「上传」到「已复核」自动计时。未复核的零件图不计入，避免半成品拉低数据。
      </p>
      <dl className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-stone-200 bg-white px-4 py-3">
          <dt className="text-xs text-stone-500">平均处理耗时</dt>
          <dd className="mt-1 text-lg font-semibold text-stone-900">
            {formatDurationSeconds(comparison.average_processing_seconds)}
          </dd>
          <p className="mt-1 text-xs text-stone-500">已计入 {comparison.reviewed_count} 张已复核零件图</p>
        </div>
        <div className="rounded-xl border border-stone-200 bg-white px-4 py-3">
          <dt className="text-xs text-stone-500">人工基线平均</dt>
          <dd className="mt-1 text-lg font-semibold text-stone-900">
            {formatDurationSeconds(comparison.average_baseline_seconds)}
          </dd>
          <p className="mt-1 text-xs text-stone-500">已录入 {comparison.baseline_count} 条纯人工作业计时</p>
        </div>
        <div className="rounded-xl border border-stone-200 bg-white px-4 py-3">
          <dt className="text-xs text-stone-500">对照结果</dt>
          <dd className="mt-1 text-lg font-semibold text-stone-900">
            {savedLabel(comparison.saved_seconds)}
          </dd>
          <p className="mt-1 text-xs text-stone-500">
            {comparison.saved_seconds === null
              ? "需要至少一张已复核零件图和一条人工基线"
              : "基线平均减去本厂平均处理耗时"}
          </p>
        </div>
        <div className="rounded-xl border border-stone-200 bg-white px-4 py-3">
          <dt className="text-xs text-stone-500">未计入</dt>
          <dd className="mt-1 text-lg font-semibold text-stone-900">
            {comparison.excluded_unreviewed_count} 张
          </dd>
          <p className="mt-1 text-xs text-stone-500">尚未标记已复核，不进入统计</p>
        </div>
      </dl>
      <div className="mt-4 rounded-xl border border-stone-200 bg-white px-4 py-3">
        <h3 className="text-xs font-medium text-stone-500">阶段平均时长</h3>
        <dl className="mt-2 grid gap-3 sm:grid-cols-3">
          <div>
            <dt className="text-xs text-stone-500">分级</dt>
            <dd className="text-sm font-medium text-stone-900">
              {formatDurationSeconds(comparison.average_grading_seconds)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-stone-500">提取</dt>
            <dd className="text-sm font-medium text-stone-900">
              {formatDurationSeconds(comparison.average_extraction_seconds)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-stone-500">复核</dt>
            <dd className="text-sm font-medium text-stone-900">
              {formatDurationSeconds(comparison.average_review_seconds)}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}
