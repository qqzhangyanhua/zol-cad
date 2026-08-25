import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

export async function POST(): Promise<NextResponse> {
  return proxyToBackend("/auth/logout", { method: "POST" });
}
