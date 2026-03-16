import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { fetchSailingActivities } from "@/lib/api";
import Alert from "@mui/material/Alert";
import SailingLogbook from "@/components/SailingLogbook";
import mockData from "@/mock_data/mock_sailing_data.json";

export default async function SailingPage() {
  if (process.env.NEXT_PUBLIC_USE_MOCK === "true") {
    return <SailingLogbook activities={mockData.activities} />;
  }

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
