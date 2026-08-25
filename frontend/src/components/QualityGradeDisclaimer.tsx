type QualityGradeDisclaimerProps = {
  text: string;
};

export function QualityGradeDisclaimer({ text }: QualityGradeDisclaimerProps) {
  return <p className="text-xs leading-5 text-stone-500">{text}</p>;
}
