import { auth } from "@/auth";
import { fetchActivityTrack } from "@/lib/api";
import ActivityTrackCharts from "@/components/ActivityTrackCharts";
import TacksTable from "@/components/TacksTable";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import MuiLink from "@mui/material/Link";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import NextLink from "next/link";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function ActivityDetailPage({ params }: Props) {
  const { id } = await params;
  const activityId = Number(id);

  const session = await auth();
  const accessToken = (session as { accessToken?: string })?.accessToken;
  if (!accessToken) return <Typography>Not authenticated.</Typography>;

  let points, tacks;
  try {
    const data = await fetchActivityTrack(activityId, accessToken);
    points = data.points;
    tacks  = data.tacks;
  } catch {
    return (
      <Box>
        <Typography color="error">
          Could not load track data for activity {activityId}.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <MuiLink
          component={NextLink}
          href="/dashboard/sailing"
          sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
        >
          <ArrowBackIcon fontSize="small" />
          Back to Logbook
        </MuiLink>
      </Box>

      <Box>
        <Typography variant="h5" fontWeight="bold">
          Activity {activityId}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {points.length} GPS points &nbsp;·&nbsp;
          <MuiLink
            href={`https://www.strava.com/activities/${activityId}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            View on Strava
          </MuiLink>
        </Typography>
      </Box>

      <TacksTable tacks={tacks} />
      <ActivityTrackCharts points={points} />
    </Box>
  );
}
