"use client";

import dynamic from "next/dynamic";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import type { TrackPoint } from "@/lib/api";

// Plotly does not support SSR — load client-side only
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props {
  points: TrackPoint[];
}

/** Bin bearings into N equal sectors and return counts. */
function bearingHistogram(bearings: number[], sectors = 36): { theta: number[]; r: number[] } {
  const width = 360 / sectors;
  const counts = new Array(sectors).fill(0);
  for (const b of bearings) {
    if (b == null) continue;
    counts[Math.floor(((b % 360) + 360) % 360 / width)]++;
  }
  const theta = Array.from({ length: sectors }, (_, i) => i * width);
  return { theta, r: counts };
}

/** Bin rotations by bearing sector; separate port (–) and starboard (+). */
function rotationRose(
  points: TrackPoint[],
  sectors = 36,
): { theta: number[]; stbd: number[]; port: number[] } {
  const width = 360 / sectors;
  const stbd = new Array(sectors).fill(0);
  const port = new Array(sectors).fill(0);
  for (const p of points) {
    if (p.bearing_deg == null || p.rotation_deg == null) continue;
    const bin = Math.floor(((p.bearing_deg % 360) + 360) % 360 / width);
    if (p.rotation_deg >= 0) stbd[bin] += p.rotation_deg;
    else port[bin] += Math.abs(p.rotation_deg);
  }
  const theta = Array.from({ length: sectors }, (_, i) => i * width);
  return { theta, stbd, port };
}

const LAYOUT_BASE: Partial<Plotly.Layout> = {
  polar: {
    radialaxis: { visible: true, showticklabels: true },
    angularaxis: { direction: "clockwise", rotation: 90 },
  },
  showlegend: true,
  margin: { t: 40, b: 40, l: 40, r: 40 },
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
};

const CONFIG: Partial<Plotly.Config> = { displayModeBar: false, responsive: true };

export default function ActivityTrackCharts({ points }: Props) {
  const bearings = points.map((p) => p.bearing_deg).filter((b): b is number => b != null);
  const { theta: bTheta, r: bR } = bearingHistogram(bearings);
  const { theta: rTheta, stbd, port } = rotationRose(points);

  // ROT scatter: bearing vs |rate of turn|
  const rotPoints = points.filter((p) => p.bearing_deg != null && p.rot_speed_deg_min != null);
  const rotTheta = rotPoints.map((p) => p.bearing_deg as number);
  const rotR     = rotPoints.map((p) => Math.abs(p.rot_speed_deg_min as number));
  const rotColor = rotPoints.map((p) =>
    (p.rotation_deg ?? 0) >= 0 ? "#1a9850" : "#d73027",
  );

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>

      {/* 1. Bearing compass rose */}
      <Box>
        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
          Bearing Distribution (compass rose)
        </Typography>
        <Plot
          data={[{
            type: "barpolar",
            theta: bTheta,
            r: bR,
            width: 360 / 36,
            marker: { color: "#1976d2", opacity: 0.8 },
            name: "Heading",
          } as Plotly.Data]}
          layout={{ ...LAYOUT_BASE, title: "" } as Plotly.Layout}
          config={CONFIG}
          style={{ width: "100%", height: 380 }}
        />
      </Box>

      {/* 2. Rotation rose — port vs starboard by heading sector */}
      <Box>
        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
          Cumulative Rotation by Heading (port / starboard)
        </Typography>
        <Plot
          data={[
            {
              type: "barpolar",
              theta: rTheta,
              r: stbd,
              width: 360 / 36,
              marker: { color: "#388e3c", opacity: 0.75 },
              name: "Starboard (+)",
            } as Plotly.Data,
            {
              type: "barpolar",
              theta: rTheta,
              r: port,
              width: 360 / 36,
              marker: { color: "#d32f2f", opacity: 0.75 },
              name: "Port (−)",
            } as Plotly.Data,
          ]}
          layout={{ ...LAYOUT_BASE, title: "" } as Plotly.Layout}
          config={CONFIG}
          style={{ width: "100%", height: 380 }}
        />
      </Box>

      {/* 3. ROT scatter — magnitude by bearing, coloured by direction */}
      <Box>
        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
          Rate of Turn by Bearing (°/min)
        </Typography>
        <Plot
          data={[{
            type: "scatterpolar",
            theta: rotTheta,
            r: rotR,
            mode: "markers",
            marker: { color: rotColor, size: 4, opacity: 0.6 },
            name: "ROT",
          } as Plotly.Data]}
          layout={{ ...LAYOUT_BASE, title: "" } as Plotly.Layout}
          config={CONFIG}
          style={{ width: "100%", height: 380 }}
        />
      </Box>

    </Box>
  );
}
