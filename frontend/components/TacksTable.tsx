"use client";

import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Typography from "@mui/material/Typography";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import type { Tack } from "@/lib/api";

const columns: GridColDef<Tack>[] = [
  { field: "index",            headerName: "#",            width: 50 },
  {
    field: "direction",
    headerName: "Direction",
    width: 110,
    renderCell: (p) => (
      <Chip
        label={p.value}
        size="small"
        color={p.value === "starboard" ? "success" : "error"}
        variant="outlined"
      />
    ),
  },
  { field: "angle_deg",         headerName: "Angle (°)",    width: 95  },
  { field: "duration_s",        headerName: "Duration (s)", width: 110 },
  { field: "start_bearing_deg", headerName: "From (°)",     width: 90  },
  { field: "end_bearing_deg",   headerName: "To (°)",       width: 90  },
  { field: "start_speed_kn",    headerName: "Start (kn)",   width: 100 },
  { field: "avg_speed_kn",      headerName: "Avg (kn)",     width: 95  },
  { field: "end_speed_kn",      headerName: "End (kn)",     width: 95  },
];

export default function TacksTable({ tacks }: { tacks: Tack[] }) {
  if (tacks.length === 0) {
    return (
      <Box>
        <Typography variant="h6" fontWeight="bold" gutterBottom>Tacks</Typography>
        <Typography color="text.secondary">No tacks detected.</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" fontWeight="bold" gutterBottom>
        Tacks ({tacks.length})
      </Typography>
      <DataGrid
        rows={tacks}
        columns={columns}
        getRowId={(r) => r.index}
        hideFooter={tacks.length <= 100}
        disableRowSelectionOnClick
        sx={{ height: "auto" }}
      />
    </Box>
  );
}
