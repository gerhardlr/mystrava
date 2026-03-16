import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchActivities } from "@/lib/api";
import Alert from "@mui/material/Alert";
import ActivitiesTable from "@/components/ActivitiesTable";

export default async function ActivitiesPage() {
  const session = await auth();
  if (!session?.accessToken) redirect("/api/auth/signin");

  try {
    const data = await fetchActivities(session.accessToken);
    return <ActivitiesTable activities={data.activities} />;
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Failed to load activities";
    return <Alert severity="error">{msg}</Alert>;
  }
}
