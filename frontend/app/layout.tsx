import type { Metadata } from "next";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import { auth } from "@/auth";
import Providers from "@/lib/providers";

export const metadata: Metadata = {
  title: "Strava Dashboard",
  description: "View and analyse your Strava activities",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <AppRouterCacheProvider>
          <Providers session={session}>{children}</Providers>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
