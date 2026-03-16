"use client";

import { DataGrid, GridColDef } from "@mui/x-data-grid";
import type { Activity } from "@/lib/api";

const columns: GridColDef<Activity>[] = [
  { field: "id", headerName: "ID", width: 90 },
  { field: "name", headerName: "Name", flex: 1, minWidth: 160 },
  { field: "sport_type", headerName: "Type", width: 120 },
  { field: "start_date_local", headerName: "Date", width: 160 },
  {
    field: "distance_km",
    headerName: "Distance (km)",
    width: 130,
    type: "number",
  },
  {
    field: "moving_time_min",
    headerName: "Moving (min)",
    width: 130,
    type: "number",
  },
  {
    field: "elapsed_time_min",
    headerName: "Elapsed (min)",
    width: 130,
    type: "number",
  },
];

export default function ActivitiesTable({ activities }: { activities: Activity[] }) {
  return (
    <DataGrid
      rows={activities}
      columns={columns}
      pageSizeOptions={[25, 50, 100]}
      initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
      autoHeight
      disableRowSelectionOnClick
    />
  );
}
