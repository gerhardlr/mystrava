"use client";

import dynamic from "next/dynamic";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { LineChart } from "@mui/x-charts/LineChart";
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

function XYChart({
  title,
  xData,
  yData,
  yLabel,
  color,
}: {
  title: string;
  xData: number[];
  yData: (number | null)[];
  yLabel: string;
  color: string;
}) {
  return (
    <Box>
      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
        {title}
      </Typography>
      <LineChart
        xAxis={[{ data: xData, label: "Time (s)", tickMinStep: 60 }]}
        yAxis={[{ label: yLabel }]}
        series={[{ data: yData, color, showMark: false, connectNulls: false }]}
        height={260}
        margin={{ left: 60, right: 20, top: 10, bottom: 40 }}
      />
    </Box>
  );
}

export default function ActivityTrackCharts({ points }: Props) {
  const maxTime = points[points.length - 1]?.time_s ?? 1;
  const r = points.map((p) => p.time_s / maxTime);
  const bearingTheta = points.map((p) => p.bearing_deg);

  const timeAxis = points.map((p) => p.time_s);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <PolarTrace
        title="Bearing over time"
        theta={bearingTheta}
        r={r}
        color="#1976d2"
        angularLabel="heading °"
      />
      <XYChart
        title="Rotation over time"
        xData={timeAxis}
        yData={points.map((p) => p.rotation_deg)}
        yLabel="° (+ stbd)"
        color="#388e3c"
      />
      <XYChart
        title="Rate of Turn over time"
        xData={timeAxis}
        yData={points.map((p) => p.rot_speed_deg_min)}
        yLabel="°/min"
        color="#f57c00"
      />
    </Box>
  );
}
