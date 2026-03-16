import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchActivities } from "@/lib/api";
import Typography from "@mui/material/Typography";
import Grid from "@mui/material/Grid2";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Alert from "@mui/material/Alert";

export default async function DashboardPage() {
  const session = await auth();
  if (!session?.accessToken) redirect("/api/auth/signin");

  let stats = { total: 0, runs: 0, rides: 0, sails: 0, totalKm: 0 };
  let error: string | null = null;

  try {
    const data = await fetchActivities(session.accessToken);
    stats = {
      total: data.count,
      runs: data.activities.filter((a) => a.sport_type === "Run").length,
      rides: data.activities.filter((a) => a.sport_type === "Ride").length,
      sails: data.activities.filter((a) => a.sport_type === "Sail").length,
      totalKm: Math.round(
        data.activities.reduce((s, a) => s + a.distance_km, 0)
      ),
    };
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load activities";
  }

  const statCards = [
    { label: "Total Activities", value: stats.total },
    { label: "Runs", value: stats.runs },
    { label: "Rides", value: stats.rides },
    { label: "Sails", value: stats.sails },
    { label: "Total Distance (km)", value: stats.totalKm.toLocaleString() },
  ];

  return (
    <>
      <Typography variant="h5" gutterBottom>
        Welcome back{session.user?.name ? `, ${session.user.name}` : ""}!
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2}>
        {statCards.map(({ label, value }) => (
          <Grid key={label} size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h4" fontWeight="bold">
                  {value}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {label}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </>
  );
}
