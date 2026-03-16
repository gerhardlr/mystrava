"use client";

import { DataGrid, GridColDef } from "@mui/x-data-grid";
import type { SailingActivity } from "@/lib/api";

const columns: GridColDef<SailingActivity>[] = [
  { field: "start_date_local", headerName: "Date", width: 160 },
  { field: "name", headerName: "Name", flex: 1, minWidth: 160 },
  { field: "from", headerName: "From", width: 160 },
  { field: "to", headerName: "To", width: 160 },
  {
    field: "distance_nm",
    headerName: "Distance (nm)",
    width: 130,
    type: "number",
  },
  {
    field: "moving_time_hr",
    headerName: "Moving (hr)",
    width: 120,
    type: "number",
  },
  {
    field: "elapsed_time_hr",
    headerName: "Elapsed (hr)",
    width: 120,
    type: "number",
  },
  {
    field: "after_sunset_hr",
    headerName: "After Sunset (hr)",
    width: 150,
    type: "number",
  },
];

export default function SailingLogbook({
  activities,
}: {
  activities: SailingActivity[];
}) {
  return (
    <DataGrid
      rows={activities.map((a, i) => ({ id: i, ...a }))}
      columns={columns}
      pageSizeOptions={[25, 50, 100]}
      initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
      autoHeight
      disableRowSelectionOnClick
    />
  );
}
