import Link from "next/link";

import type { FactoryProcessingRecord } from "@/lib/types";

type FactoryProcessingRecordTableProps = {
  items: FactoryProcessingRecord[];
};

export function FactoryProcessingRecordTable({ items }: FactoryProcessingRecordTableProps) {
  if (items.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-stone-200 bg-white px-4 py-10 text-center text-sm text-stone-500">
        本厂还没有处理记录。
      </p>
    );
  }
  return (
    <section className="overflow-hidden rounded-xl border border-stone-200 bg-white">
      <table className="w-full text-left text-sm">
        <thead className="bg-stone-50 text-xs text-stone-500">
          <tr>
            <th className="px-4 py-2 font-medium">零件图</th>
            <th className="px-4 py-2 font-medium">处理人</th>
            <th className="px-4 py-2 font-medium">状态</th>
            <th className="px-4 py-2 font-medium">上传时间</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.part_drawing_id} className="border-t border-stone-100">
              <td className="px-4 py-2.5">
                <Link href={`/part-drawings/${item.part_drawing_id}`} className="text-stone-900 hover:underline">
                  {item.original_filename}
                </Link>
              </td>
              <td className="px-4 py-2.5 text-stone-600">{item.uploaded_by_username ?? "—"}</td>
              <td className="px-4 py-2.5 text-stone-600">{item.status}</td>
              <td className="px-4 py-2.5 text-stone-500">
                {new Date(item.uploaded_at).toLocaleString("zh-CN")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
