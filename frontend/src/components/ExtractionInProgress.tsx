"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

type ExtractionInProgressProps = {
  drawingId: string;
};

export function ExtractionInProgress({ drawingId }: ExtractionInProgressProps) {
  const router = useRouter();

  useEffect(() => {
    const timer = window.setInterval(() => {
      router.refresh();
    }, 1000);
    return () => window.clearInterval(timer);
  }, [drawingId, router]);

  return (
    <div className="rounded-lg border border-stone-200 bg-white px-4 py-6">
      <p className="text-sm font-medium text-stone-900">正在处理零件图</p>
      <p className="mt-1 text-xs leading-5 text-stone-500">
        系统正在做图纸质量分级并读图取数。请稍候，完成后会在左侧预填表单。
      </p>
    </div>
  );
}
