import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function POST(request: Request): Promise<NextResponse> {
  const body: unknown = await request.json();
  return proxyToBackend("/manual-baselines", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}
