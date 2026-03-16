const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.API_URL ??
  "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types matching the FastAPI response shapes
// ---------------------------------------------------------------------------

export interface Activity {
  id: number;
  name: string;
  sport_type: string;
  start_date_local: string;
  start_lat?: number | null;
  start_lon?: number | null;
  distance_km: number;
  moving_time_min: number;
  elapsed_time_min: number;
}

export interface SailingActivity {
  id?: number;
  name: string;
  sport_type?: string;
  start_date_local: string;
  distance_nm: number;
  moving_time_hr: number;
  elapsed_time_hr: number;
  after_sunset_hr?: number | null;
  max_speed_kn?: number | null;
  avg_speed_kn?: number | null;
  from?: string | null;
  to?: string | null;
}

export interface ActivitiesResponse {
  activities: Activity[];
  count: number;
}

export interface SailingResponse {
  activities: SailingActivity[];
  count: number;
}

// ---------------------------------------------------------------------------
// Fetch helpers
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, accessToken: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    // Disable Next.js full-route cache so data is always fresh
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export function fetchActivities(accessToken: string): Promise<ActivitiesResponse> {
  return apiFetch<ActivitiesResponse>("/api/activities", accessToken);
}

export function fetchSailingActivities(accessToken: string): Promise<SailingResponse> {
  return apiFetch<SailingResponse>("/api/activities/sailing", accessToken);
}
