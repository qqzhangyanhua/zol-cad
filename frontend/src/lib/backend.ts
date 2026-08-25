import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { SESSION_COOKIE, backendUrl } from "@/lib/constants";

export async function fetchBackend(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;
  const headers = new Headers(init.headers);
  if (token && !headers.has("cookie")) {
    headers.set("cookie", `${SESSION_COOKIE}=${token}`);
  }
  return fetch(`${backendUrl()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}

export async function proxyToBackend(
  path: string,
  init: RequestInit = {},
): Promise<NextResponse> {
  const upstream = await fetchBackend(path, init);
  const body = await upstream.arrayBuffer();
  const response = new NextResponse(body, { status: upstream.status });
  const contentType = upstream.headers.get("content-type");
  if (contentType) {
    response.headers.set("content-type", contentType);
  }
  for (const cookie of upstream.headers.getSetCookie()) {
    response.headers.append("set-cookie", cookie);
  }
  return response;
}
