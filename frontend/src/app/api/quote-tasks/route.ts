import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function GET(request: Request): Promise<NextResponse> {
  const query = new URL(request.url).search;
  return proxyToBackend(`/quote-tasks${query}`, { method: "GET" });
}

export async function POST(request: Request): Promise<NextResponse> {
  const body = await request.text();
  return proxyToBackend("/quote-tasks", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });
}
