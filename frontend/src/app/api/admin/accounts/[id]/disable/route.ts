import { NextResponse } from "next/server";

import { proxyToBackend } from "@/lib/backend";

type DisableAccountRouteProps = {
  params: Promise<{ id: string }>;
};

export async function POST(
  _request: Request,
  { params }: DisableAccountRouteProps,
): Promise<NextResponse> {
  const { id } = await params;
  return proxyToBackend(`/admin/accounts/${id}/disable`, { method: "POST" });
}
