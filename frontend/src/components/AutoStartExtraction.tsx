"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { ExtractionInProgress } from "@/components/ExtractionInProgress";
import { readErrorDetail } from "@/lib/types";

type AutoStartExtractionProps = {
  drawingId: string;
};

export function AutoStartExtraction({ drawingId }: AutoStartExtractionProps) {
  const router = useRouter();
  const started = useRef(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (started.current) {
      return;
    }
    started.current = true;
    void (async () => {
      const response = await fetch(`/api/part-drawings/${drawingId}/extract`, { method: "POST" });
      const payload: unknown = await response.json().catch(() => null);
      if (response.status === 409) {
        router.refresh();
        return;
      }
      if (!response.ok) {
        setError(readErrorDetail(payload) ?? "无法开始读图取数");
        return;
      }
      router.refresh();
    })();
  }, [drawingId, router]);

  if (error) {
    return (
      <p className="text-sm text-red-700" role="alert">
        {error}
      </p>
    );
  }
  return <ExtractionInProgress drawingId={drawingId} />;
}
