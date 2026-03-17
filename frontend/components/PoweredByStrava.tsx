import Image from "next/image";
import Box from "@mui/material/Box";

export default function PoweredByStrava() {
  return (
    <Box sx={{ p: 2, display: "flex", justifyContent: "flex-end" }}>
      <a href="https://www.strava.com" target="_blank" rel="noopener noreferrer">
        <Image
          src="/strava-logos/api_logo_pwrdBy_strava_horiz_white.svg"
          alt="Powered by Strava"
          width={150}
          height={40}
        />
      </a>
    </Box>
  );
}
