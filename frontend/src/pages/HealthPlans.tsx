import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Button,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Chip,
  Alert,
  Snackbar,
  CircularProgress,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material'
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid'
import { API_ENDPOINTS, apiRequest } from '../config/api'

interface HealthPlan {
  id: number
  name: string
  operator_code: string
  registration_number: string
  active: boolean
}

const HealthPlans: React.FC = () => {
  const [open, setOpen] = useState(false)
  const [editingPlan, setEditingPlan] = useState<HealthPlan | null>(null)
  const [healthPlans, setHealthPlans] = useState<HealthPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [planToDelete, setPlanToDelete] = useState<HealthPlan | null>(null)

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'operator_code', headerName: 'Operator Code', width: 150 },
    { field: 'registration_number', headerName: 'Registration', width: 150 },
    {
      field: 'active',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 100,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => handleEdit(params.row)}
        />,
                 <GridActionsCellItem
           icon={<DeleteIcon />}
           label="Delete"
           onClick={() => handleDelete(params.row)}
         />,
      ],
    },
  ]

  const handleOpen = () => setOpen(true)
  const handleClose = () => {
    setOpen(false)
    setEditingPlan(null)
  }

  const handleEdit = (plan: HealthPlan) => {
    setEditingPlan(plan)
    setOpen(true)
  }

  // Load health plans from backend API
  useEffect(() => {
    loadHealthPlans()
  }, [])

  const loadHealthPlans = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiRequest(API_ENDPOINTS.HEALTH_PLANS)
      setHealthPlans(response.items || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load health plans')
      console.error('Error loading health plans:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = (plan: HealthPlan) => {
    setPlanToDelete(plan)
    setDeleteModalOpen(true)
  }

  const confirmDelete = async () => {
    if (!planToDelete) return
    
    try {
      setSubmitting(true)
      setError(null)
      await apiRequest(`${API_ENDPOINTS.HEALTH_PLANS}/${planToDelete.id}`, { method: 'DELETE' })
      setHealthPlans(healthPlans.filter(p => p.id !== planToDelete.id))
      setSuccess('Health plan deleted successfully')
      setDeleteModalOpen(false)
      setPlanToDelete(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete health plan')
      console.error('Error deleting health plan:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const cancelDelete = () => {
    setDeleteModalOpen(false)
    setPlanToDelete(null)
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const formData = new FormData(event.target as HTMLFormElement)
    
    try {
      setSubmitting(true)
      setError(null)
      
      const planData = {
        name: formData.get('name') as string,
        operator_code: formData.get('operator_code') as string,
        registration_number: formData.get('registration_number') as string,
        active: true,
      }
      
      if (editingPlan) {
        // Update existing health plan
        await apiRequest(`${API_ENDPOINTS.HEALTH_PLANS}/${editingPlan.id}`, {
          method: 'PUT',
          body: JSON.stringify(planData)
        })
        setSuccess('Health plan updated successfully')
      } else {
        // Add new health plan
        await apiRequest(API_ENDPOINTS.HEALTH_PLANS, {
          method: 'POST',
          body: JSON.stringify(planData)
        })
        setSuccess('Health plan created successfully')
      }
      
      // Reload health plans from database
      await loadHealthPlans()
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save health plan')
      console.error('Error saving health plan:', err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Health Insurance Plans</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpen}
        >
          Add Health Plan
        </Button>
      </Box>

      {/* Loading and Error States */}
      {loading && (
        <Box display="flex" justifyContent="center" alignItems="center" height={200}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Health Plans Data Grid */}
      {!loading && (
        <Paper sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={healthPlans}
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
      )}

      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingPlan ? 'Edit Health Plan' : 'Add New Health Plan'}
        </DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  name="name"
                  label="Plan Name"
                  placeholder="Enter health plan name"
                  fullWidth
                  required
                  defaultValue={editingPlan?.name || ''}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  name="operator_code"
                  label="Operator Code"
                  placeholder="Enter operator code"
                  fullWidth
                  required
                  defaultValue={editingPlan?.operator_code || ''}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  name="registration_number"
                  label="Registration Number"
                  placeholder="Enter registration number"
                  fullWidth
                  required
                  defaultValue={editingPlan?.registration_number || ''}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button type="submit" variant="contained">
              {editingPlan ? 'Update' : 'Create'}
            </Button>
          </DialogActions>
        </form>
             </Dialog>

       {/* Delete Confirmation Modal */}
       <Dialog open={deleteModalOpen} onClose={cancelDelete} maxWidth="sm" fullWidth>
         <DialogTitle>
           Confirm Delete
         </DialogTitle>
         <DialogContent>
           <Typography>
             Are you sure you want to delete health plan <strong>{planToDelete?.name}</strong>?
           </Typography>
           <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
             This action cannot be undone.
           </Typography>
         </DialogContent>
         <DialogActions>
           <Button onClick={cancelDelete} color="primary">
             Cancel
           </Button>
           <Button 
             onClick={confirmDelete} 
             color="error" 
             variant="contained"
             disabled={submitting}
           >
             {submitting ? <CircularProgress size={20} /> : 'Delete'}
           </Button>
         </DialogActions>
       </Dialog>

       {/* Success/Error Snackbar */}
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert onClose={() => setSuccess(null)} severity="success">
          {success}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert onClose={() => setError(null)} severity="error">
          {error}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default HealthPlans 