import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function GET(): Promise<NextResponse> {
  return proxyToBackend("/processing-time", { method: "GET" });
}
