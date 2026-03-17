"use client";

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { LineChart } from "@mui/x-charts/LineChart";
import type { TrackPoint } from "@/lib/api";

interface Props {
  points: TrackPoint[];
}

function TrackChart({
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
  const xData = points.map((p) => p.time_s);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <TrackChart
        title="Bearing"
        xData={xData}
        yData={points.map((p) => p.bearing_deg)}
        yLabel="° (0=N)"
        color="#1976d2"
      />
      <TrackChart
        title="Rotation"
        xData={xData}
        yData={points.map((p) => p.rotation_deg)}
        yLabel="° (+ stbd)"
        color="#388e3c"
      />
      <TrackChart
        title="Rate of Turn"
        xData={xData}
        yData={points.map((p) => p.rot_speed_deg_min)}
        yLabel="°/min"
        color="#f57c00"
      />
    </Box>
  );
}
