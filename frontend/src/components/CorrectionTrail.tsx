import type { CorrectionRecord, ExtractedField } from "@/lib/types";

type CorrectionTrailProps = {
  records: CorrectionRecord[];
  fields: ExtractedField[];
  actorNames: Readonly<Record<string, string>>;
};

function sortNewestFirst(records: CorrectionRecord[]): CorrectionRecord[] {
  return [...records].sort((left, right) => {
    const byTime = right.occurred_at.localeCompare(left.occurred_at);
    if (byTime !== 0) {
      return byTime;
    }
    return right.id.localeCompare(left.id);
  });
}

function fieldLabel(record: CorrectionRecord, fields: ExtractedField[]): string {
  const exact = fields.find((field) => field.key === record.field_key);
  if (exact !== undefined) {
    return exact.label;
  }
  const addedIndex = record.field_key.indexOf("__added__");
  if (addedIndex > 0) {
    const baseKey = record.field_key.slice(0, addedIndex);
    const base = fields.find((field) => field.key === baseKey);
    if (base !== undefined) {
      return base.label;
    }
  }
  return record.field_type;
}

function displayValue(value: string | null): string {
  if (value === null || value === "") {
    return "（空）";
  }
  return value;
}

function actorLabel(actorUserId: string, actorNames: Readonly<Record<string, string>>): string {
  return actorNames[actorUserId] ?? `账号 ${actorUserId.slice(0, 8)}`;
}

export function CorrectionTrail({ records, fields, actorNames }: CorrectionTrailProps) {
  const ordered = sortNewestFirst(records);

  return (
    <details className="glass-card mt-4">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-3.5 text-sm marker:content-none [&::-webkit-details-marker]:hidden">
        <span className="font-bold text-slate-800">修正记录</span>
        <span className="text-xs text-slate-500">
          {ordered.length === 0 ? "无改动 · 展开查看" : `${ordered.length} 条 · 展开查看`}
        </span>
      </summary>
      <div className="border-t border-slate-100/80 px-5 pb-5 pt-3">
        <p className="text-xs text-slate-500">
          报价员对提取值的改动留痕。补录项的原值为空。最新的改动在前。
        </p>
        {ordered.length === 0 ? (
          <p className="mt-3 rounded-xl border border-dashed border-slate-200 bg-slate-50/80 px-4 py-8 text-center text-sm text-slate-500">
            这张零件图还没有修正记录。提取值未被改过，或尚未开始复核。
          </p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[40rem] text-left text-sm">
              <caption className="sr-only">本张零件图的修正记录，按时间倒序</caption>
              <thead className="text-xs text-slate-500">
                <tr>
                  <th className="py-2 pr-3 font-medium">字段</th>
                  <th className="py-2 pr-3 font-medium">字段类型</th>
                  <th className="py-2 pr-3 font-medium">原值 → 新值</th>
                  <th className="py-2 pr-3 font-medium">操作人</th>
                  <th className="py-2 font-medium">时间</th>
                </tr>
              </thead>
              <tbody>
                {ordered.map((record) => (
                  <tr key={record.id} className="border-t border-slate-100 align-top text-slate-800">
                    <td className="py-2.5 pr-3">{fieldLabel(record, fields)}</td>
                    <td className="py-2.5 pr-3 text-slate-600">{record.field_type}</td>
                    <td className="py-2.5 pr-3">
                      <span className="text-slate-500">{displayValue(record.old_value)}</span>
                      <span className="mx-1.5 text-slate-400">→</span>
                      <span className="font-medium">{displayValue(record.new_value)}</span>
                    </td>
                    <td className="py-2.5 pr-3 text-slate-600">{actorLabel(record.actor_user_id, actorNames)}</td>
                    <td className="py-2.5 text-slate-500">
                      {new Date(record.occurred_at).toLocaleString("zh-CN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </details>
  );
}
