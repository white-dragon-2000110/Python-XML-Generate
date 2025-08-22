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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material'
import { DataGrid, GridColDef, GridActionsCellItem } from '@mui/x-data-grid'
import { API_ENDPOINTS, apiRequest } from '../config/api'

interface Provider {
  id: number
  name: string
  cnpj: string
  type: string
  address: string
  contact: string
  active: boolean
}

const Providers: React.FC = () => {
  const [open, setOpen] = useState(false)
  const [editingProvider, setEditingProvider] = useState<Provider | null>(null)
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [providerToDelete, setProviderToDelete] = useState<Provider | null>(null)

  // Provider type options
  const providerTypes = [
    'hospital',
    'clinic',
    'laboratory',
    'imaging_center',
    'specialist',
    'general_practitioner',
    'pharmacy',
    'ambulance',
    'other'
  ]

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'cnpj', headerName: 'CNPJ', width: 150 },
    { field: 'type', headerName: 'Type', width: 120 },
    { field: 'address', headerName: 'Address', width: 250 },
    { field: 'contact', headerName: 'Contact', width: 150 },
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
    setEditingProvider(null)
  }

  const handleEdit = (provider: Provider) => {
    setEditingProvider(provider)
    setOpen(true)
  }

  // Load providers from backend API
  useEffect(() => {
    loadProviders()
  }, [])

  const loadProviders = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiRequest(API_ENDPOINTS.PROVIDERS)
      setProviders(response.items || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load providers')
      console.error('Error loading providers:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = (provider: Provider) => {
    setProviderToDelete(provider)
    setDeleteModalOpen(true)
  }

  const confirmDelete = async () => {
    if (!providerToDelete) return
    
    try {
      setSubmitting(true)
      setError(null)
      
      // Delete the provider
      await apiRequest(`${API_ENDPOINTS.PROVIDERS}/${providerToDelete.id}`, { method: 'DELETE' })
      
      // Remove from local state
      setProviders(providers.filter(p => p.id !== providerToDelete.id))
      setSuccess('Provider deleted successfully')
      setDeleteModalOpen(false)
      setProviderToDelete(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete provider'
      setError(errorMessage)
      console.error('Error deleting provider:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const cancelDelete = () => {
    setDeleteModalOpen(false)
    setProviderToDelete(null)
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const formData = new FormData(event.target as HTMLFormElement)
    
    try {
      setSubmitting(true)
      setError(null)
      
      // Basic validation
      const name = formData.get('name') as string
      const cnpj = formData.get('cnpj') as string
      const type = formData.get('type') as string
      const address = formData.get('address') as string
      const contact = formData.get('contact') as string
      
      // Validate required fields
      if (!name || !cnpj || !type || !address || !contact) {
        throw new Error('All required fields must be filled')
      }
      
      // Validate CNPJ format
      if (!/^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$/.test(cnpj)) {
        throw new Error('CNPJ must be in format: 00.000.000/0000-00')
      }
      
      // Validate provider type
      if (!providerTypes.includes(type)) {
        throw new Error('Please select a valid provider type')
      }
      
      // Validate address length
      if (address.length < 10) {
        throw new Error('Address must be at least 10 characters long')
      }
      
      // Validate contact length
      if (contact.length < 5) {
        throw new Error('Contact name must be at least 5 characters long')
      }
      
      const providerData = {
        name,
        cnpj,
        type,
        address,
        contact,
        active: true,
      }
      
      if (editingProvider) {
        // Update existing provider
        await apiRequest(`${API_ENDPOINTS.PROVIDERS}/${editingProvider.id}`, {
          method: 'PUT',
          body: JSON.stringify(providerData)
        })
        setSuccess('Provider updated successfully')
      } else {
        // Add new provider
        await apiRequest(API_ENDPOINTS.PROVIDERS, {
          method: 'POST',
          body: JSON.stringify(providerData)
        })
        setSuccess('Provider created successfully')
      }
      
      // Reload providers from database
      await loadProviders()
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save provider')
      console.error('Error saving provider:', err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Healthcare Providers</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpen}
        >
          Add Provider
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

      {/* Providers Data Grid */}
      {!loading && (
        <Paper sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={providers}
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
          {editingProvider ? 'Edit Provider' : 'Add New Provider'}
        </DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  name="name"
                  label="Provider Name"
                  placeholder="Enter provider name"
                  fullWidth
                  required
                  defaultValue={editingProvider?.name || ''}
                  helperText="Minimum 3 characters"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  name="cnpj"
                  label="CNPJ"
                  placeholder="00.000.000/0000-00"
                  fullWidth
                  required
                  defaultValue={editingProvider?.cnpj || ''}
                  helperText="Format: 00.000.000/0000-00"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>Provider Type</InputLabel>
                  <Select
                    name="type"
                    label="Provider Type"
                    defaultValue={editingProvider?.type || 'hospital'}
                  >
                    {providerTypes.map((type) => (
                      <MenuItem key={type} value={type}>
                        {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  name="contact"
                  label="Contact Person"
                  placeholder="Enter contact person name"
                  fullWidth
                  required
                  defaultValue={editingProvider?.contact || ''}
                  helperText="Minimum 5 characters"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  name="address"
                  label="Address"
                  placeholder="Enter full address (minimum 10 characters)"
                  fullWidth
                  required
                  defaultValue={editingProvider?.address || ''}
                  helperText="Address must be at least 10 characters long"
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose} disabled={submitting}>Cancel</Button>
            <Button 
              type="submit" 
              variant="contained"
              disabled={submitting}
              startIcon={submitting ? <CircularProgress size={20} /> : null}
            >
              {submitting ? 'Saving...' : (editingProvider ? 'Update' : 'Create')}
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
             Are you sure you want to delete provider <strong>{providerToDelete?.name}</strong>?
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

export default Providers 