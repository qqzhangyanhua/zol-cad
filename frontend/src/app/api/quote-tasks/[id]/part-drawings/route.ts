import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function POST(request: Request, context: RouteContext): Promise<NextResponse> {
  const { id } = await context.params;
  const body = await request.text();
  return proxyToBackend(`/quote-tasks/${id}/part-drawings`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });
}
