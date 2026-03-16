import NextAuth from "next-auth";
import { authConfig } from "@/auth.config";

export const { auth: middleware } = NextAuth(authConfig);

export const config = {
  // Protect all /dashboard routes; let everything else through
  matcher: ["/dashboard/:path*"],
};
