import React from 'react'
import { Paper, Box, CircularProgress } from '@mui/material'
import { DataGrid, GridColDef } from '@mui/x-data-grid'

interface DataTableProps {
  rows: any[]
  columns: GridColDef[]
  loading: boolean
  height?: number
  aspectRatio?: string
}

const DataTable: React.FC<DataTableProps> = ({
  rows,
  columns,
  loading,
  height = 600,
  aspectRatio = '16/9'
}) => {
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={200}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Paper sx={{ 
      height, 
      width: '100%',
      aspectRatio,
      borderRadius: 3,
      overflow: 'hidden'
    }}>
      <DataGrid
        rows={rows}
        columns={columns}
        pageSizeOptions={[5, 10, 25]}
        initialState={{
          pagination: {
            paginationModel: { page: 0, pageSize: 10 },
          },
        }}
        disableRowSelectionOnClick
      />
    </Paper>
  )
}

export default DataTable 