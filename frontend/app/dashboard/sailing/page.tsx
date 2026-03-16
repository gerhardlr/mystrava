import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchSailingActivities } from "@/lib/api";
import Alert from "@mui/material/Alert";
import SailingLogbook from "@/components/SailingLogbook";

export default async function SailingPage() {
  const session = await auth();
  if (!session?.accessToken) redirect("/api/auth/signin");

  try {
    const data = await fetchSailingActivities(session.accessToken);
    return <SailingLogbook activities={data.activities} />;
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Failed to load sailing activities";
    return <Alert severity="error">{msg}</Alert>;
  }
}
