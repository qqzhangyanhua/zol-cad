import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function POST(): Promise<NextResponse> {
  return proxyToBackend("/admin/tenant-data/delete-challenge", { method: "POST" });
}
