type PageLoadingProps = {
  label: string;
};

export function PageLoading({ label }: PageLoadingProps) {
  return (
    <div
      className="flex h-screen w-full gap-3 overflow-hidden p-3 md:gap-4 md:p-4"
      role="status"
      aria-live="polite"
      aria-label={label}
    >
      <div className="glass-panel w-64 shrink-0 animate-pulse rounded-3xl" />
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div className="glass-card h-16 animate-pulse" />
        <div className="glass-card flex flex-1 flex-col justify-center p-8">
          <div className="mx-auto h-3 w-40 animate-pulse rounded-full bg-slate-200/80" />
          <p className="mt-4 text-center text-sm text-slate-500">{label}</p>
          <div className="mx-auto mt-6 h-24 w-full max-w-xl animate-pulse rounded-2xl bg-slate-200/60" />
        </div>
      </div>
    </div>
  );
}
