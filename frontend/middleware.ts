export { auth as middleware } from "@/auth";

export const config = {
  // Protect all /dashboard routes; let everything else through
  matcher: ["/dashboard/:path*"],
};
