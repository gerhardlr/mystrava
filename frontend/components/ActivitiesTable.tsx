"use client";

import { DataGrid, GridColDef } from "@mui/x-data-grid";
import type { Activity } from "@/lib/api";
import { ActivityRow } from "@/lib/activity-values";

const columns: GridColDef[] = [
  { field: "id",               headerName: "ID",       width: 90 },
  { field: "name",             headerName: "Name",     flex: 1, minWidth: 160 },
  { field: "sport_type",       headerName: "Type",     width: 120 },
  { field: "start_date_local", headerName: "Date",     width: 170 },
  { field: "distance",         headerName: "Distance", width: 110 },
  { field: "moving",           headerName: "Moving",   width: 100 },
  { field: "elapsed",          headerName: "Elapsed",  width: 100 },
];

export default function ActivitiesTable({ activities }: { activities: Activity[] }) {
  const rows = activities.map((a) =>
    ActivityRow.fromActivity(a).render()
  );

  return (
    <DataGrid
      rows={rows}
      columns={columns}
      pageSizeOptions={[25, 50, 100]}
      initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
      sx={{ height: "100%" }}
      disableRowSelectionOnClick
    />
  );
}
