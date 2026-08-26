import { presentConfidentialityNotice } from "@/lib/confidentiality-copy";
import type { ConfidentialityNotice as ConfidentialityNoticeData } from "@/lib/types";

type ConfidentialityNoticeProps = {
  notice: ConfidentialityNoticeData;
};

export function ConfidentialityNotice({ notice }: ConfidentialityNoticeProps) {
  const view = presentConfidentialityNotice(notice);

  return (
    <div className="flex flex-col gap-5">
      <section className="rounded-lg border border-stone-200 bg-white p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-stone-900">供应商选定现状</h2>
          <span
            className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
              view.vendorSelected
                ? "bg-emerald-50 text-emerald-800"
                : "bg-amber-50 text-amber-800"
            }`}
          >
            {view.vendorSelected ? "已选定" : "尚未选定"}
          </span>
        </div>
        <p className="mt-2 text-sm text-stone-700">{view.vendorStatus}</p>
        <dl className="mt-3 grid gap-2 text-sm text-stone-600">
          <div>
            <dt className="font-medium text-stone-800">决定状态</dt>
            <dd>{view.decisionStatus}</dd>
          </div>
          <div>
            <dt className="font-medium text-stone-800">当前提取引擎</dt>
            <dd>{view.extractionEngine}</dd>
          </div>
        </dl>
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-stone-900">图纸存在哪</h2>
        <p className="mt-2 text-sm text-stone-700">{view.drawingLocation}</p>
        <p className="mt-1 text-xs text-stone-500">{view.drawingNotes}</p>
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-stone-900">由谁处理</h2>
        <p className="mt-2 text-sm text-stone-700">{view.processorSummary}</p>
        <p className="mt-2 text-xs text-stone-500">
          当前决定：{view.decisionLine}（{view.decisionLineNote}）
        </p>
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-stone-900">三条硬门槛</h2>
        <table className="mt-3 w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-stone-200 text-stone-500">
              <th className="py-2 pr-3 font-medium">门槛</th>
              <th className="py-2 pr-3 font-medium">判定</th>
              <th className="py-2 font-medium">证据</th>
            </tr>
          </thead>
          <tbody>
            {view.hardGates.map((gate) => (
              <tr key={gate.key} className="border-b border-stone-100 align-top">
                <td className="py-2 pr-3 text-stone-800">{gate.name}</td>
                <td className="py-2 pr-3 text-stone-700">{gate.verdict}</td>
                <td className="py-2 text-stone-600">{gate.evidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-3 text-sm text-stone-700">{view.trainingStatement}</p>
        <p className="mt-1 text-sm text-stone-700">{view.dpaStatement}</p>
        {view.implementationConstraints.length > 0 ? (
          <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-stone-500">
            {view.implementationConstraints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4">
        <h2 className="text-sm font-semibold text-stone-900">阅读约定</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-stone-700">
          {view.caveats.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
