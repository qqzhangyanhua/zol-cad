type AssemblyOutOfScopeNoticeProps = {
  text: string;
};

export function AssemblyOutOfScopeNotice({ text }: AssemblyOutOfScopeNoticeProps) {
  return (
    <p className="rounded-lg bg-stone-100 px-3 py-2 text-xs leading-5 text-stone-700" role="status">
      {text}
    </p>
  );
}
