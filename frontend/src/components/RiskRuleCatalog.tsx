import type { RiskRule } from "@/lib/types";

type RiskRuleCatalogProps = {
  items: RiskRule[];
};

export function RiskRuleCatalog({ items }: RiskRuleCatalogProps) {
  return (
    <section className="rounded-xl border border-stone-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-stone-900">当前生效的风险规则</h2>
      <p className="mt-1 text-xs text-stone-500">
        只读。规则由规则引擎算出，永不输出「无风险 / 安全」。阈值仍是暂定值，不是票 01 样本结论。
      </p>
      <table className="mt-3 w-full text-left text-sm">
        <thead className="text-xs text-stone-500">
          <tr>
            <th className="py-2 font-medium">标签</th>
            <th className="py-2 font-medium">规则</th>
            <th className="py-2 font-medium">阈值</th>
          </tr>
        </thead>
        <tbody>
          {items.map((rule) => (
            <tr key={rule.rule_id} className="border-t border-stone-100 align-top">
              <td className="py-2.5 text-stone-900">{rule.label_name}</td>
              <td className="py-2.5 font-mono text-xs text-stone-600">{rule.rule_id}</td>
              <td className="py-2.5">
                <p className="text-stone-800">{rule.threshold}</p>
                <p className="mt-1 text-xs leading-5 text-stone-500">{rule.description}</p>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
