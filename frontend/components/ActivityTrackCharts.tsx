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

const LAYOUT_BASE: Partial<Plotly.Layout> = {
  polar: {
    radialaxis: { visible: true, showticklabels: false },
    angularaxis: { direction: "clockwise", rotation: 90 },
  },
  showlegend: false,
  margin: { t: 20, b: 20, l: 40, r: 40 },
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
};

const CONFIG: Partial<Plotly.Config> = { displayModeBar: false, responsive: true };

function PolarTrace({
  title,
  theta,
  r,
  color,
  angularLabel,
}: {
  title: string;
  theta: (number | null)[];
  r: number[];
  color: string;
  angularLabel?: string;
}) {
  return (
    <Box>
      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
        {title}
        {angularLabel && (
          <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
            (angle = {angularLabel}, radius = time)
          </Typography>
        )}
      </Typography>
      <Plot
        data={[
          {
            type: "scatterpolar",
            theta,
            r,
            mode: "lines",
            line: {
              color,
              width: 1.5,
            },
          } as Plotly.Data,
          // Mark start and end points
          {
            type: "scatterpolar",
            theta: [theta[0], theta[theta.length - 1]],
            r: [r[0], r[r.length - 1]],
            mode: "markers",
            marker: {
              color: ["#4caf50", "#f44336"],
              size: 8,
              symbol: ["circle", "square"],
            },
            hovertext: ["Start", "End"],
            hoverinfo: "text",
          } as Plotly.Data,
        ]}
        layout={LAYOUT_BASE as Plotly.Layout}
        config={CONFIG}
        style={{ width: "100%", height: 400 }}
      />
    </Box>
  );
}

export default function ActivityTrackCharts({ points }: Props) {
  // Radius is normalised elapsed time so all three plots share the same scale
  const maxTime = points[points.length - 1]?.time_s ?? 1;
  const r = points.map((p) => p.time_s / maxTime);

  // Bearing: 0–360° clockwise from north — maps directly onto polar angle
  const bearingTheta = points.map((p) => p.bearing_deg);

  // Rotation: –180 to +180 → wrap into 0–360 so polar axis is continuous
  const rotationTheta = points.map((p) =>
    p.rotation_deg != null ? ((p.rotation_deg % 360) + 360) % 360 : null,
  );

  // Rate of turn: same wrapping as rotation
  const rotSpeedTheta = points.map((p) =>
    p.rot_speed_deg_min != null ? ((p.rot_speed_deg_min % 360) + 360) % 360 : null,
  );

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <PolarTrace
        title="Bearing over time"
        theta={bearingTheta}
        r={r}
        color="#1976d2"
        angularLabel="heading °"
      />
      <PolarTrace
        title="Rotation over time"
        theta={rotationTheta}
        r={r}
        color="#388e3c"
        angularLabel="rotation °"
      />
      <PolarTrace
        title="Rate of Turn over time"
        theta={rotSpeedTheta}
        r={r}
        color="#f57c00"
        angularLabel="ROT °/min"
      />
    </Box>
  );
}
