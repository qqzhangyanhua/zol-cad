"use client";

import { ZoomPanViewport } from "@/components/ZoomPanViewport";

type OriginalDrawingViewerProps = {
  src: string;
  contentType: string;
  filename: string;
};

export function OriginalDrawingViewer({
  src,
  contentType,
  filename,
}: OriginalDrawingViewerProps) {
  const isPdf = contentType === "application/pdf" || filename.toLowerCase().endsWith(".pdf");

  return (
    <ZoomPanViewport>
      {isPdf ? (
        <iframe
          title={filename}
          src={src}
          className="h-[80vh] w-[min(100%,72rem)] bg-white shadow-sm"
        />
      ) : (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt={filename} className="max-h-[80vh] max-w-[min(100%,72rem)] select-none" />
      )}
    </ZoomPanViewport>
  );
}
