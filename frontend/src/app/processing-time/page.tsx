import { redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
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
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">处理耗时</h1>
          <p className="mt-1 text-sm text-stone-500">
            用本厂已复核零件图的客观计时，对照试用初期录入的纯人工基线，判断这工具到底省没省时间。
          </p>
        </div>
        <ProcessingTimeSummary comparison={comparison} />
        <ProcessingTimeTable items={comparison.items} />
        <section aria-labelledby="manual-baseline-heading">
          <h2 id="manual-baseline-heading" className="text-sm font-semibold text-stone-900">
            人工基线
          </h2>
          <p className="mt-1 text-xs text-stone-500">
            请录入几条完全不借助本工具的作业计时。对照只看客观数据，不靠问卷或印象。
          </p>
          <ManualBaselineForm />
          <ManualBaselineList items={comparison.baselines} />
        </section>
      </main>
    </div>
  );
}
