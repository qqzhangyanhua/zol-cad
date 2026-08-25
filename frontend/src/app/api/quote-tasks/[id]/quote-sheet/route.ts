import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function GET(request: Request, context: RouteContext): Promise<NextResponse> {
  const { id } = await context.params;
  const incoming = new URL(request.url);
  const format = incoming.searchParams.get("format") ?? "xlsx";
  const query = new URLSearchParams({ format });
  return proxyToBackend(`/quote-tasks/${id}/quote-sheet?${query.toString()}`, { method: "GET" });
}
