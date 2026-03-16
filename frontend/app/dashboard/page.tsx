import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchSailingActivities } from "@/lib/api";
import { ActivityRow, Speed } from "@/lib/activity-values";
import Typography from "@mui/material/Typography";
import Grid from "@mui/material/Grid2";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Alert from "@mui/material/Alert";

export default async function DashboardPage() {
  const session = await auth();
  if (!session?.accessToken) redirect("/api/auth/signin");

  let statCards: { label: string; value: string | number }[] = [];
  let error: string | null = null;

  try {
    const sailingData = await fetchSailingActivities(session.accessToken);
    const sailRows    = sailingData.activities.map((a, i) => ActivityRow.fromSailingActivity(a, i));

    const totalNm       = ActivityRow.sum(sailRows, "distance").toFixed(1);
    const typicalSailStart = ActivityRow.typicalTime(sailRows.map((r) => r.from?.value)) ?? "—";
    const typicalSailEnd   = ActivityRow.typicalTime(sailRows.map((r) => r.to?.value.to)) ?? "—";
    const medianSpeed      = ActivityRow.median(sailRows.map((r) => r.avgSpeed?.value));
    const typicalSpeed     = medianSpeed != null ? new Speed(medianSpeed).render() : "—";

    statCards = [
{ label: "Total Sailed Activities", value: sailRows.length },
      { label: "Total Sailed (nm)",       value: `${totalNm} nm` },
      { label: "Typical Sail Start",      value: typicalSailStart },
      { label: "Typical Sail End",        value: typicalSailEnd },
      { label: "Typical Speed",           value: typicalSpeed },
    ];
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load activities";
  }

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
          <Grid key={label} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
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
