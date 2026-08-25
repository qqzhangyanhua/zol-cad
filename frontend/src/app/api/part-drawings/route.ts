import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function GET(): Promise<NextResponse> {
  return proxyToBackend("/part-drawings", { method: "GET" });
}

export async function POST(request: Request): Promise<NextResponse> {
  const formData = await request.formData();
  return proxyToBackend("/part-drawings", {
    method: "POST",
    body: formData,
  });
}
