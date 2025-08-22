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
  MenuItem,
  Chip,
  Alert,
  Snackbar,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material'
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid'
import { API_ENDPOINTS, apiRequest } from '../config/api'

interface Claim {
  id: number
  patient_id: number
  provider_id: number
  plan_id: number
  claim_date: string
  value: number
  status: string
}

interface Patient {
  id: number
  name: string
}

interface Provider {
  id: number
  name: string
}

interface HealthPlan {
  id: number
  name: string
}

const Claims: React.FC = () => {
  const [open, setOpen] = useState(false)
  const [editingClaim, setEditingClaim] = useState<Claim | null>(null)
  const [claims, setClaims] = useState<Claim[]>([])
  const [patients, setPatients] = useState<Patient[]>([])
  const [providers, setProviders] = useState<Provider[]>([])
  const [healthPlans, setHealthPlans] = useState<HealthPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [claimToDelete, setClaimToDelete] = useState<Claim | null>(null)

  const statusOptions = ['pending', 'approved', 'denied', 'paid']

  // Helper functions to get names from IDs
  const getPatientName = (patientId: number) => {
    const patient = patients.find(p => p.id === patientId)
    return patient ? patient.name : `Patient #${patientId}`
  }

  const getProviderName = (providerId: number) => {
    const provider = providers.find(p => p.id === providerId)
    return provider ? provider.name : `Provider #${providerId}`
  }

  // Load claims from backend API
  useEffect(() => {
    loadClaims()
  }, [])

  const loadClaims = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch all data in parallel
      const [claimsRes, patientsRes, providersRes, healthPlansRes] = await Promise.all([
        apiRequest(API_ENDPOINTS.CLAIMS),
        apiRequest(API_ENDPOINTS.PATIENTS),
        apiRequest(API_ENDPOINTS.PROVIDERS),
        apiRequest(API_ENDPOINTS.HEALTH_PLANS),
      ])
      
      setClaims(claimsRes.items || [])
      setPatients(patientsRes.items || [])
      setProviders(providersRes.items || [])
      setHealthPlans(healthPlansRes.items || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load claims')
      console.error('Error loading claims:', err)
    } finally {
      setLoading(false)
    }
  }

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { 
      field: 'patient_id', 
      headerName: 'Patient Name', 
      width: 200,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 500 }}>
          {getPatientName(params.value)}
        </Typography>
      )
    },
    { 
      field: 'provider_id', 
      headerName: 'Provider Name', 
      width: 200,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 500 }}>
          {getProviderName(params.value)}
        </Typography>
      )
    },
    { field: 'claim_date', headerName: 'Claim Date', width: 120 },
    { 
      field: 'value', 
      headerName: 'Claim Value', 
      width: 120,
      valueFormatter: (params) => {
        if (params.value) {
          const amount = parseFloat(params.value);
          return isNaN(amount) ? params.value : `$${amount.toFixed(2)}`;
        }
        return '$0.00';
      },
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => {
        const color = 
          params.value === 'approved' ? 'success' :
          params.value === 'denied' ? 'error' :
          params.value === 'paid' ? 'info' : 'default'
        return (
          <Chip
            label={params.value}
            color={color}
            size="small"
          />
        )
      },
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 150,
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
    setEditingClaim(null)
  }

  const handleEdit = (claim: Claim) => {
    setEditingClaim(claim)
    setOpen(true)
  }

  const handleDelete = (claim: Claim) => {
    setClaimToDelete(claim)
    setDeleteModalOpen(true)
  }

  const confirmDelete = async () => {
    if (!claimToDelete) return
    
    try {
      setSubmitting(true)
      setError(null)
      await apiRequest(`${API_ENDPOINTS.CLAIMS}/${claimToDelete.id}`, { method: 'DELETE' })
      setClaims(claims.filter(c => c.id !== claimToDelete.id))
      setSuccess('Claim deleted successfully')
      setDeleteModalOpen(false)
      setClaimToDelete(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete claim')
      console.error('Error deleting claim:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const cancelDelete = () => {
    setDeleteModalOpen(false)
    setClaimToDelete(null)
  }



  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const formData = new FormData(event.target as HTMLFormElement)
    
    try {
      setSubmitting(true)
      setError(null)
      
      // Basic validation
      const patient_id = formData.get('patient_id') as string
      const provider_id = formData.get('provider_id') as string
      const plan_id = formData.get('plan_id') as string
      const claim_date = formData.get('claim_date') as string
      const value = formData.get('value') as string
      const status = formData.get('status') as string

      // Validate required fields
      if (!patient_id || !provider_id || !plan_id || !claim_date || !value) {
        throw new Error('All required fields must be filled')
      }

      const claimData = {
        patient_id: parseInt(patient_id),
        provider_id: parseInt(provider_id),
        plan_id: parseInt(plan_id),
        claim_date,
        value: parseFloat(value),
        status,
      }
      
      if (editingClaim) {
        // Update existing claim
        await apiRequest(`${API_ENDPOINTS.CLAIMS}/${editingClaim.id}`, {
          method: 'PUT',
          body: JSON.stringify(claimData)
        })
        setSuccess('Claim updated successfully')
      } else {
        // Add new claim
        await apiRequest(API_ENDPOINTS.CLAIMS, {
          method: 'POST',
          body: JSON.stringify(claimData)
        })
        setSuccess('Claim created successfully')
      }
      
      // Reload claims from database
      await loadClaims()
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save claim')
      console.error('Error saving claim:', err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Claims</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpen}
        >
          Add Claim
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

      {/* Claims Data Grid */}
      {!loading && (
        <Paper sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={claims}
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
          {editingClaim ? 'Edit Claim' : 'Add New Claim'}
        </DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>Patient</InputLabel>
                  <Select
                    name="patient_id"
                    label="Patient"
                    defaultValue={editingClaim?.patient_id || ''}
                  >
                    {patients.map((patient) => (
                      <MenuItem key={patient.id} value={patient.id}>
                        {patient.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>Provider</InputLabel>
                  <Select
                    name="provider_id"
                    label="Provider"
                    defaultValue={editingClaim?.provider_id || ''}
                  >
                    {providers.map((provider) => (
                      <MenuItem key={provider.id} value={provider.id}>
                        {provider.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>Health Plan</InputLabel>
                  <Select
                    name="plan_id"
                    label="Health Plan"
                    defaultValue={editingClaim?.plan_id || ''}
                  >
                    {healthPlans.map((plan) => (
                      <MenuItem key={plan.id} value={plan.id}>
                        {plan.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  name="claim_date"
                  label="Claim Date"
                  type="date"
                  fullWidth
                  required
                  defaultValue={editingClaim?.claim_date || ''}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  name="value"
                  label="Claim Value"
                  placeholder="0.00"
                  type="number"
                  fullWidth
                  required
                  defaultValue={editingClaim?.value || ''}
                  inputProps={{ step: 0.01, min: 0 }}
                  helperText="Claim amount in decimal format"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  name="status"
                  label="Status"
                  select
                  fullWidth
                  required
                  defaultValue={editingClaim?.status || 'pending'}
                >
                  {statusOptions.map((option) => (
                    <MenuItem key={option} value={option}>
                      {option.charAt(0).toUpperCase() + option.slice(1)}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button type="submit" variant="contained">
              {editingClaim ? 'Update' : 'Create'}
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
                           Are you sure you want to delete claim <strong>#{claimToDelete?.id}</strong>?
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

export default Claims 