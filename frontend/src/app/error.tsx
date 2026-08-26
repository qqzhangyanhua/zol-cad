"use client";

import { useEffect } from "react";
import { ServiceUnavailable } from "@/components/ServiceUnavailable";

type AppErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function AppError({ error, reset }: AppErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return <ServiceUnavailable error={error} onRetry={reset} />;
}
