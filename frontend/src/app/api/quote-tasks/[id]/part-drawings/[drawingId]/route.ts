import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

type RouteContext = {
  params: Promise<{ id: string; drawingId: string }>;
};

export async function DELETE(_request: Request, context: RouteContext): Promise<NextResponse> {
  const { id, drawingId } = await context.params;
  return proxyToBackend(`/quote-tasks/${id}/part-drawings/${drawingId}`, { method: "DELETE" });
}
