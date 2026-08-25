import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { SESSION_COOKIE } from "@/lib/constants";

export function proxy(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;
  const hasSession = request.cookies.has(SESSION_COOKIE);
  const isLogin = pathname === "/login";

  if (!hasSession && !isLogin) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }
  if (hasSession && isLogin) {
    return NextResponse.redirect(new URL("/part-drawings", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
