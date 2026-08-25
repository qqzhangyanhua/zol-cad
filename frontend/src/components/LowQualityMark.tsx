type LowQualityMarkProps = {
  text: string;
};

export function LowQualityMark({ text }: LowQualityMarkProps) {
  return (
    <p className="inline-flex rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-800" role="status">
      {text}
    </p>
  );
}
