import type { NextAuthConfig } from "next-auth";
import Strava from "next-auth/providers/strava";

export const authConfig: NextAuthConfig = {
  providers: [
    Strava({
      clientId: process.env.STRAVA_CLIENT_ID!,
      clientSecret: process.env.STRAVA_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    authorized({ auth }) {
      return !!auth?.user;
    },
  },
};
