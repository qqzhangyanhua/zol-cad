import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

type RouteContext = {
  params: Promise<{ key: string[] }>;
};

export async function GET(request: Request, context: RouteContext): Promise<NextResponse> {
  const { key } = await context.params;
  const search = new URL(request.url).search;
  return proxyToBackend(`/object-store/${key.join("/")}${search}`, { method: "GET" });
}
