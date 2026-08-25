type ExtractionDisclaimerProps = {
  text: string;
};

export function ExtractionDisclaimer({ text }: ExtractionDisclaimerProps) {
  return (
    <div
      role="note"
      className="sticky top-0 z-20 border-b border-amber-200 bg-amber-50 px-6 py-2.5"
    >
      <p className="text-sm leading-6 text-amber-950">{text}</p>
    </div>
  );
}
