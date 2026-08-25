import { ContinueDespiteQualityButton } from "@/components/ContinueDespiteQualityButton";

type PoorDrawingAdviseProps = {
  drawingId: string;
  message: string;
};

export function PoorDrawingAdvise({ drawingId, message }: PoorDrawingAdviseProps) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-3">
      <p className="text-sm leading-6 text-red-950">{message}</p>
      <div className="mt-3">
        <ContinueDespiteQualityButton drawingId={drawingId} />
      </div>
    </div>
  );
}
