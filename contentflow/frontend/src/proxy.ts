import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedPaths = ["/generate", "/history", "/brands", "/schedules", "/calendar", "/settings"];
const authPaths = ["/login", "/register"];

export function proxy(request: NextRequest) {
  const token = request.cookies.get("access_token")?.value;
  const path = request.nextUrl.pathname;

  if (protectedPaths.some((p) => path.startsWith(p)) && !token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (authPaths.some((p) => path.startsWith(p)) && token) {
    return NextResponse.redirect(new URL("/generate", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/generate/:path*", "/history/:path*", "/brands/:path*", "/schedules/:path*", "/calendar/:path*", "/settings/:path*", "/login", "/register"],
};
