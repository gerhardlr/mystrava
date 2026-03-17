"use client";

import dynamic from "next/dynamic";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import type { TrackPoint, Tack } from "@/lib/api";

// Plotly does not support SSR — load client-side only
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props {
  points: TrackPoint[];
  tacks: Tack[];
}

const LAYOUT_BASE: Partial<Plotly.Layout> = {
  polar: {
    radialaxis: { visible: true, showticklabels: false },
    angularaxis: { direction: "clockwise", rotation: 90 },
  },
  showlegend: true,
  legend: { orientation: "h", y: -0.1 },
  margin: { t: 20, b: 60, l: 40, r: 40 },
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
};

const CONFIG: Partial<Plotly.Config> = { displayModeBar: false, responsive: true };

interface Segment {
  theta: (number | null)[];
  r: number[];
  color: string;
  name: string;
}

function buildBearingSegments(points: TrackPoint[], tacks: Tack[], maxTime: number): Segment[] {
  if (tacks.length === 0) {
    return [{
      theta: points.map((p) => p.bearing_deg),
      r:     points.map((p) => p.time_s / maxTime),
      color: "#1976d2",
      name:  "Sailing",
    }];
  }

  const sorted = [...tacks].sort((a, b) => a.start_time_s - b.start_time_s);
  const segments: Segment[] = [];
  let cursor = 0;

  const slice = (from: number, to: number): Segment["theta"] =>
    points.slice(from, to + 1).map((p) => p.bearing_deg);
  const rSlice = (from: number, to: number): number[] =>
    points.slice(from, to + 1).map((p) => p.time_s / maxTime);

  for (const tack of sorted) {
    const si = points.findIndex((p) => p.time_s >= tack.start_time_s);
    const ei = points.findLastIndex((p) => p.time_s <= tack.end_time_s);
    if (si === -1 || ei === -1 || ei < si) continue;

    // Normal segment up to tack start (overlap by 1 point for a connected line)
    if (si > cursor) {
      segments.push({ theta: slice(cursor, si), r: rSlice(cursor, si), color: "#1976d2", name: "Sailing" });
    }

    // Tack segment
    const color = tack.direction === "port" ? "#d32f2f" : "#2e7d32";
    const label = tack.direction === "port" ? "Port tack" : "Stbd tack";
    segments.push({ theta: slice(si, ei), r: rSlice(si, ei), color, name: label });

    cursor = ei;
  }

  // Remaining normal segment after last tack
  if (cursor < points.length - 1) {
    segments.push({ theta: slice(cursor, points.length - 1), r: rSlice(cursor, points.length - 1), color: "#1976d2", name: "Sailing" });
  }

  return segments;
}

function XYChart({
  title,
  xData,
  yData,
  yLabel,
  color,
  tacks = [],
}: {
  title: string;
  xData: number[];
  yData: (number | null)[];
  yLabel: string;
  color: string;
  tacks?: Tack[];
}) {
  const shapes: Partial<Plotly.Shape>[] = tacks.map((t) => ({
    type: "rect",
    xref: "x",
    yref: "paper",
    x0: t.start_time_s,
    x1: t.end_time_s,
    y0: 0,
    y1: 1,
    fillcolor: t.direction === "port" ? "#d32f2f" : "#2e7d32",
    opacity: 0.5,
    line: { width: 0 },
  }));

  const annotations: Partial<Plotly.Annotations>[] = tacks.map((t) => ({
    x: (t.start_time_s + t.end_time_s) / 2,
    yref: "paper",
    y: 1,
    text: `T${t.index}`,
    showarrow: false,
    font: { size: 10 },
    yanchor: "bottom",
  }));

  return (
    <Box>
      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
        {title}
      </Typography>
      <Plot
        data={[{
          type: "scatter",
          x: xData,
          y: yData,
          mode: "lines",
          line: { color, width: 1.5 },
          connectgaps: false,
        } as Plotly.Data]}
        layout={{
          xaxis: { title: { text: "Time (s)" } },
          yaxis: { title: { text: yLabel } },
          shapes,
          annotations,
          margin: { t: 20, b: 50, l: 60, r: 20 },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          showlegend: false,
        } as unknown as Plotly.Layout}
        config={CONFIG}
        style={{ width: "100%", height: 280 }}
      />
    </Box>
  );
}

export default function ActivityTrackCharts({ points, tacks }: Props) {
  const maxTime = points[points.length - 1]?.time_s ?? 1;
  const segments = buildBearingSegments(points, tacks, maxTime);
  const timeAxis = points.map((p) => p.time_s);

  // Deduplicate legend entries (multiple normal/tack segments → one legend item each)
  const seen = new Set<string>();
  const traces: Plotly.Data[] = segments.map((seg) => {
    const showlegend = !seen.has(seg.name);
    seen.add(seg.name);
    return {
      type: "scatterpolar",
      theta: seg.theta,
      r: seg.r,
      mode: "lines",
      line: { color: seg.color, width: 1.5 },
      name: seg.name,
      showlegend,
    } as Plotly.Data;
  });

  // Start / end markers
  traces.push({
    type: "scatterpolar",
    theta: [points[0].bearing_deg, points[points.length - 1].bearing_deg],
    r: [0, 1],
    mode: "markers",
    marker: { color: ["#4caf50", "#f44336"], size: 8, symbol: ["circle", "square"] },
    hovertext: ["Start", "End"],
    hoverinfo: "text",
    showlegend: false,
  } as Plotly.Data);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <Box>
        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
          Bearing over time
          <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
            (angle = heading °, radius = time)
          </Typography>
        </Typography>
        <Plot
          data={traces}
          layout={LAYOUT_BASE as Plotly.Layout}
          config={CONFIG}
          style={{ width: "100%", height: 420 }}
        />
      </Box>

      <XYChart
        title="Rotation over time"
        xData={timeAxis}
        yData={points.map((p) => p.rotation_deg)}
        yLabel="° (+ stbd)"
        color="#388e3c"
        tacks={tacks}
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
