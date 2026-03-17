"use client";
import Image from "next/image";
import Box from "@mui/material/Box";
import { useColorScheme } from "@mui/material/styles";

export default function PoweredByStrava() {
  const { mode, systemMode } = useColorScheme();
  const resolved = mode === "system" ? systemMode : mode;
  const logo =
    resolved === "dark"
      ? "/strava-logos/api_logo_pwrdBy_strava_horiz_white.svg"
      : "/strava-logos/api_logo_pwrdBy_strava_horiz_black.svg";

  return (
    <Box sx={{ p: 2, display: "flex", justifyContent: "flex-end" }}>
      <a href="https://www.strava.com" target="_blank" rel="noopener noreferrer">
        <Image src={logo} alt="Powered by Strava" width={150} height={40} />
      </a>
    </Box>
  );
}
