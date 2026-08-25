export function EmptyPartDrawingState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-16 text-center">
      <h2 className="text-lg font-semibold text-stone-900">你还没有上传过零件图</h2>
      <p className="mt-2 max-w-sm text-sm leading-6 text-stone-500">
        当前工厂还没有任何零件图。把 PDF 或图片拖到上方即可开始。
      </p>
    </div>
  );
}
