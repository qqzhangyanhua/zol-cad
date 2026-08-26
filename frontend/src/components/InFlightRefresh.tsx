"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { isInFlightPartDrawingStatus, type PartDrawingStatus } from "@/lib/types";

type InFlightRefreshProps = {
  statuses: readonly PartDrawingStatus[];
};

export function InFlightRefresh({ statuses }: InFlightRefreshProps) {
  const router = useRouter();
  const shouldPoll = statuses.some(isInFlightPartDrawingStatus);

  useEffect(() => {
    if (!shouldPoll) {
      return;
    }
    const timer = window.setInterval(() => {
      router.refresh();
    }, 1000);
    return () => window.clearInterval(timer);
  }, [shouldPoll, router]);

  return null;
}
