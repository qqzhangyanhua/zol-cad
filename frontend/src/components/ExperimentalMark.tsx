type ExperimentalMarkProps = {
  text: string;
};

export function ExperimentalMark({ text }: ExperimentalMarkProps) {
  return (
    <p
      className="inline-flex rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-950"
      role="status"
    >
      {text}
    </p>
  );
}
