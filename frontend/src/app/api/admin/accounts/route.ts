import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function GET(): Promise<NextResponse> {
  return proxyToBackend("/admin/accounts");
}

export async function POST(request: Request): Promise<NextResponse> {
  const body = await request.text();
  return proxyToBackend("/admin/accounts", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });
}
