import { RetryExtractionButton } from "@/components/RetryExtractionButton";

type ExtractionFailedPanelProps = {
  drawingId: string;
  reason: string;
};

export function ExtractionFailedPanel({ drawingId, reason }: ExtractionFailedPanelProps) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-4">
      <p className="text-sm font-medium text-red-950">读图取数失败</p>
      <p className="mt-1 text-sm leading-6 text-red-900">{reason}</p>
      <p className="mt-2 text-xs text-red-800">已保存的零件图不必重新上传，可直接重试。</p>
      <div className="mt-3">
        <RetryExtractionButton drawingId={drawingId} />
      </div>
    </div>
  );
}
