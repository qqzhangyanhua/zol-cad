import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function PUT(request: Request): Promise<NextResponse> {
  const body = await request.text();
  return proxyToBackend("/admin/common-materials", {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body,
  });
}
