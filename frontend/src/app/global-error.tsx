"use client";

import { useEffect } from "react";
import { ServiceUnavailable } from "@/components/ServiceUnavailable";

import "./globals.css";

type GlobalErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="zh-CN">
      <body className="min-h-full glass-shell font-sans text-slate-800 antialiased">
        <ServiceUnavailable error={error} onRetry={reset} />
      </body>
    </html>
  );
}
