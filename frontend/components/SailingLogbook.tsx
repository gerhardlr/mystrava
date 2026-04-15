"use client";

import { DataGrid, GridColDef } from "@mui/x-data-grid";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid2";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import DownloadIcon from "@mui/icons-material/Download";
import { useRouter } from "next/navigation";
import type { SailingActivity } from "@/lib/api";
import { downloadActivityGpx } from "@/lib/api";
import { ActivityRow } from "@/lib/activity-values";

export { formatDate, formatTime, formatTo } from "@/lib/format";
import { formatMonthYear } from "@/lib/format";

function makeColumns(accessToken: string | undefined): GridColDef[] {
  return [
  { field: "start_date_local", headerName: "Date",         width: 170 },
  {
    field: "name", headerName: "Name", flex: 1, minWidth: 160,
    renderCell: (params) => params.row._nameValue?.render(params.row.strava_id),
  },
  { field: "from",             headerName: "From",         width: 80 },
  { field: "to",               headerName: "To",           width: 100 },
  { field: "distance",         headerName: "Distance",     width: 110 },
  { field: "moving",           headerName: "Moving",       width: 100 },
  { field: "elapsed",          headerName: "Elapsed",      width: 100 },
  { field: "after_sunset",     headerName: "After Sunset", width: 120 },
  { field: "max_speed",        headerName: "Max Speed",    width: 110 },
  { field: "avg_speed",        headerName: "Avg Speed",    width: 110 },
  {
    field: "_gpx",
    headerName: "",
    width: 50,
    sortable: false,
    disableColumnMenu: true,
    renderCell: (params) =>
      accessToken && params.row.strava_id ? (
        <Tooltip title="Download GPX">
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              downloadActivityGpx(params.row.strava_id, accessToken).catch(console.error);
            }}
          >
            <DownloadIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      ) : null,
  },
];};

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Box sx={{ p: 2, border: 1, borderColor: "divider", borderRadius: 1 }}>
      <Typography variant="h5" fontWeight="bold">{value}</Typography>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
    </Box>
  );
}

export default function SailingLogbook({
  activities,
  accessToken,
}: {
  activities: SailingActivity[];
  accessToken?: string;
}) {
  const router = useRouter();
  const columns = makeColumns(accessToken);
  const activityRows = activities.map((a, i) =>
    ActivityRow.fromSailingActivity(a, i)
  );

  const totalDistance  = ActivityRow.sum(activityRows, "distance").toFixed(1);
  const totalHours     = ActivityRow.sum(activityRows, "elapsed").toFixed(1);
  const nightHours     = ActivityRow.sum(activityRows, "afterSunset").toFixed(1);
  const range          = ActivityRow.dateRange(activityRows);
  const period         = range
    ? `${formatMonthYear(range.from.value)} — ${formatMonthYear(range.to.value)}`
    : "—";

  const rows = activityRows.map((r) => r.render());

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12 }}>
          <StatCard label="Period over which data was collected" value={period} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard label="Total Distance" value={`${totalDistance} nm`} />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard label="Total Hours Sailed" value={`${totalHours} hr`} />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard label="Night Hours Sailed" value={`${nightHours} hr`} />
        </Grid>

      </Grid>

      <DataGrid
        rows={rows}
        columns={columns}
        pageSizeOptions={[25, 50, 100]}
        initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        onRowClick={(params) => {
          if (params.row.strava_id) {
            router.push(`/dashboard/sailing/${params.row.strava_id}`);
          }
        }}
        sx={{ height: "100%", "& .MuiDataGrid-row": { cursor: "pointer" } }}
      />
    </Box>
  );
}
