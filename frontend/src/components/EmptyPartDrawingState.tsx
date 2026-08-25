export function EmptyPartDrawingState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-24 text-center">
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-stone-100 text-stone-400">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className="h-8 w-8"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M7.5 3.75h6.75L19.5 9v11.25A1.5 1.5 0 0 1 18 21.75H7.5A1.5 1.5 0 0 1 6 20.25V5.25A1.5 1.5 0 0 1 7.5 3.75Z"
          />
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.25 3.75V9H19.5" />
        </svg>
      </div>
      <h2 className="text-lg font-semibold text-stone-900">你还没有上传过零件图</h2>
      <p className="mt-2 max-w-sm text-sm leading-6 text-stone-500">
        当前工厂还没有任何零件图。上传会在后续版本开放。
      </p>
    </div>
  );
}
