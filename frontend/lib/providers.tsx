"use client";

import * as React from "react";
import { AppProvider } from "@toolpad/core/AppProvider";
import { SessionProvider, signIn, signOut } from "next-auth/react";
import type { Session } from "next-auth";
import DashboardIcon from "@mui/icons-material/Dashboard";
import DirectionsRunIcon from "@mui/icons-material/DirectionsRun";
import SailingIcon from "@mui/icons-material/Sailing";
import type { Navigation } from "@toolpad/core";
import theme from "@/lib/theme";

const NAVIGATION: Navigation = [
  {
    kind: "header",
    title: "Main",
  },
  {
    segment: "dashboard",
    title: "Dashboard",
    icon: <DashboardIcon />,
  },
  {
    segment: "dashboard/activities",
    title: "All Activities",
    icon: <DirectionsRunIcon />,
  },
  {
    segment: "dashboard/sailing",
    title: "Sailing Logbook",
    icon: <SailingIcon />,
  },
];

const AUTHENTICATION = { signIn, signOut };

export default function Providers({
  children,
  session,
}: {
  children: React.ReactNode;
  session: Session | null;
}) {
  return (
    <SessionProvider session={session}>
      <AppProvider
        session={session}
        authentication={AUTHENTICATION}
        navigation={NAVIGATION}
        theme={theme}
        branding={{
          title: "Strava Dashboard",
          logo: (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="#FC5200">
              <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066l-2.024 4.116z" />
              <path d="M7.488 7.344l2.083 4.109h4.171L7.488 0 2.337 11.453h4.170z" />
            </svg>
          ),
        }}
      >
        {children}
      </AppProvider>
    </SessionProvider>
  );
}
