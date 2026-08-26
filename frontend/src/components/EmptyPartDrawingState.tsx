export function EmptyPartDrawingState() {
  return (
    <div className="glass-card flex flex-1 flex-col items-center justify-center p-12 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-500 mb-3 shadow-xs">
        <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M8.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z" />
          <path d="M21 15l-5-5L5 21" />
        </svg>
      </div>
      <h2 className="text-base font-bold text-slate-800">暂无零件图数据</h2>
      <p className="mt-1.5 max-w-sm text-xs leading-5 text-slate-500">
        把 CAD 图纸、PDF 或高清零件图拖拽到上方上传区，系统将自动进行分级与特征解析。
      </p>
    </div>
  );
}
