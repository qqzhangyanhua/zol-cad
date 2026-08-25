import type { PartDrawing } from "@/lib/types";

type PartDrawingListProps = {
  items: PartDrawing[];
};

export function PartDrawingList({ items }: PartDrawingListProps) {
  return (
    <ul className="divide-y divide-stone-200 border-t border-stone-200">
      {items.map((item) => (
        <li key={item.id} className="flex items-center justify-between px-6 py-4">
          <span className="text-sm font-medium text-stone-900">
            {item.original_filename}
          </span>
          <time className="text-xs text-stone-500" dateTime={item.uploaded_at}>
            {new Date(item.uploaded_at).toLocaleString("zh-CN")}
          </time>
        </li>
      ))}
    </ul>
  );
}
