import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

type RouteContext = {
  params: Promise<{ id: string; fieldKey: string }>;
};

export async function POST(_request: Request, context: RouteContext): Promise<NextResponse> {
  const { id, fieldKey } = await context.params;
  return proxyToBackend(`/part-drawings/${id}/fields/${fieldKey}/ignore`, { method: "POST" });
}
