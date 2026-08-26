import { redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
import { ManualBaselineForm } from "@/components/ManualBaselineForm";
import { ManualBaselineList } from "@/components/ManualBaselineList";
import { ProcessingTimeSummary } from "@/components/ProcessingTimeSummary";
import { ProcessingTimeTable } from "@/components/ProcessingTimeTable";
import { fetchBackend } from "@/lib/backend";
import { parseCurrentUser, parseProcessingTimeComparison } from "@/lib/types";

export default async function ProcessingTimePage() {
  const [meResponse, comparisonResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend("/processing-time"),
  ]);

  if (meResponse.status === 401 || comparisonResponse.status === 401) {
    redirect("/login");
  }
  if (comparisonResponse.status === 403) {
    redirect("/part-drawings");
  }
  if (!meResponse.ok || !comparisonResponse.ok) {
    throw new Error("无法读取处理耗时对照");
  }

  const user = parseCurrentUser(await meResponse.json());
  const comparison = parseProcessingTimeComparison(await comparisonResponse.json());

  return (
    <AppShell user={user}>
      <AppHeader
        title="工时与处理耗时评估"
        subtitle="对照纯人工与智能辅助作业时长，评估综合提效幅度"
      />
      <main className="flex flex-1 flex-col gap-6 pb-6">
        <ProcessingTimeSummary comparison={comparison} />
        <div className="glass-card p-5 backdrop-blur-xl">
          <div className="mb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">零件图处理明细</h3>
          </div>
          <ProcessingTimeTable items={comparison.items} />
        </div>
        <section aria-labelledby="manual-baseline-heading" className="glass-card p-5 backdrop-blur-xl space-y-4">
          <div>
            <h2 id="manual-baseline-heading" className="text-sm font-bold text-slate-900">
              纯人工作业基线录入
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              录入未借助系统时的实际耗时样本，为效能对比提供客观标准
            </p>
          </div>
          <ManualBaselineForm />
          <ManualBaselineList items={comparison.baselines} />
        </section>
      </main>
    </AppShell>
  );
}
