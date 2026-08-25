import type { ConfidentialityNotice as ConfidentialityNoticeData } from "@/lib/types";

type ConfidentialityNoticeProps = {
  notice: ConfidentialityNoticeData;
};

export function ConfidentialityNotice({ notice }: ConfidentialityNoticeProps) {
  return (
    <div className="flex flex-col gap-5">
      <section className="rounded-lg border border-stone-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-stone-900">票 02 / ADR-0009 现状</h2>
        <p className="mt-2 text-sm text-stone-700">{notice.ticket_02_status}</p>
        <dl className="mt-3 grid gap-2 text-sm text-stone-600">
          <div>
            <dt className="font-medium text-stone-800">ADR 状态</dt>
            <dd>{notice.adr_status}</dd>
          </div>
          <div>
            <dt className="font-medium text-stone-800">ADR 路径</dt>
            <dd className="break-all font-mono text-xs">{notice.adr_path}</dd>
          </div>
          <div>
            <dt className="font-medium text-stone-800">调研笔记</dt>
            <dd className="break-all font-mono text-xs">{notice.research_notes_path}</dd>
          </div>
          <div>
            <dt className="font-medium text-stone-800">当前提取引擎开关</dt>
            <dd>{notice.current_extraction_engine}</dd>
          </div>
        </dl>
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-stone-900">图纸存在哪</h2>
        <p className="mt-2 text-sm text-stone-700">{notice.drawing_storage.location_summary}</p>
        <p className="mt-1 text-xs text-stone-500">{notice.drawing_storage.notes}</p>
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-stone-900">由谁处理</h2>
        <p className="mt-2 text-sm text-stone-700">{notice.processor_summary}</p>
        <p className="mt-2 text-xs text-stone-500">
          ADR 决定行：{notice.vendor_decision_line}
          {notice.selected_vendor ? `（已选定：${notice.selected_vendor}）` : "（未选定）"}
        </p>
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-stone-900">三条硬门槛（来自 ADR-0009）</h2>
        <table className="mt-3 w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-stone-200 text-stone-500">
              <th className="py-2 pr-3 font-medium">门槛</th>
              <th className="py-2 pr-3 font-medium">判定</th>
              <th className="py-2 font-medium">证据</th>
            </tr>
          </thead>
          <tbody>
            {notice.hard_gates.map((gate) => (
              <tr key={gate.key} className="border-b border-stone-100 align-top">
                <td className="py-2 pr-3 text-stone-800">{gate.name}</td>
                <td className="py-2 pr-3 text-stone-700">{gate.verdict}</td>
                <td className="py-2 text-stone-600">{gate.evidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-3 text-sm text-stone-700">{notice.used_for_training_statement}</p>
        <p className="mt-1 text-sm text-stone-700">{notice.dpa_statement}</p>
        {notice.implementation_constraints.length > 0 ? (
          <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-stone-500">
            {notice.implementation_constraints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4">
        <h2 className="text-sm font-semibold text-stone-900">阅读约定</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-stone-700">
          {notice.caveats.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
