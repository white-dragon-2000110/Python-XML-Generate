import React, { useState, useEffect } from 'react'
import { Box, Alert, CircularProgress } from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material'
import { GridColDef, GridActionsCellItem } from '@mui/x-data-grid'
import { API_ENDPOINTS, apiRequest } from '../config/api'
import { 
  DataTable, 
  PageHeader, 
  StatusAlert, 
  DeleteConfirmationModal 
} from '../components/common'
import { PatientForm } from '../components/patients'

interface Patient {
  id: number
  name: string
  cpf: string
  birth_date: string
  address: string
  phone: string
  email: string
  status: string
}

const Patients: React.FC = () => {
  const [open, setOpen] = useState(false)
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null)
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [patientToDelete, setPatientToDelete] = useState<Patient | null>(null)

  // Load patients from backend API
  useEffect(() => {
    loadPatients()
  }, [])

  const loadPatients = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiRequest(API_ENDPOINTS.PATIENTS)
      setPatients(response.items || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load patients')
      console.error('Error loading patients:', err)
    } finally {
      setLoading(false)
    }
  }

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'cpf', headerName: 'CPF', width: 150 },
    { field: 'birth_date', headerName: 'Birth Date', width: 120 },
    { field: 'phone', headerName: 'Phone', width: 150 },
    { field: 'email', headerName: 'Email', width: 200 },
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
    setEditingPatient(null)
  }

  const handleEdit = (patient: Patient) => {
    setEditingPatient(patient)
    setOpen(true)
  }

  const handleDelete = (patient: Patient) => {
    setPatientToDelete(patient)
    setDeleteModalOpen(true)
  }

  const confirmDelete = async () => {
    if (!patientToDelete) return
    
    try {
      setSubmitting(true)
      setError(null)
      await apiRequest(`${API_ENDPOINTS.PATIENTS}/${patientToDelete.id}`, { method: 'DELETE' })
      setPatients(patients.filter(p => p.id !== patientToDelete.id))
      setSuccess('Patient deleted successfully')
      setDeleteModalOpen(false)
      setPatientToDelete(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete patient')
      console.error('Error deleting patient:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const cancelDelete = () => {
    setDeleteModalOpen(false)
    setPatientToDelete(null)
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const formData = new FormData(event.target as HTMLFormElement)
    
    try {
      setSubmitting(true)
      setError(null)
      
      // Basic validation
      const name = formData.get('name') as string
      const cpf = formData.get('cpf') as string
      const birth_date = formData.get('birth_date') as string
      const address = formData.get('address') as string
      const phone = formData.get('phone') as string
      const email = formData.get('email') as string
      
      // Validate required fields
      if (!name || !cpf || !birth_date || !address || !phone || !email) {
        throw new Error('All fields are required')
      }
      
      // Validate CPF format
      if (!/^\d{3}\.\d{3}\.\d{3}-\d{2}$/.test(cpf)) {
        throw new Error('CPF must be in format: 000.000.000-00')
      }
      
      // Validate email format
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        throw new Error('Please enter a valid email address')
      }
      
      // Validate address length
      if (address.length < 10) {
        throw new Error('Address must be at least 10 characters long')
      }
      
      const patientData = {
        name,
        cpf,
        birth_date,
        address,
        phone,
        email,
      }
      
      if (editingPatient) {
        // Update existing patient
        await apiRequest(`${API_ENDPOINTS.PATIENTS}/${editingPatient.id}`, {
          method: 'PUT',
          body: JSON.stringify(patientData)
        })
        setSuccess('Patient updated successfully')
      } else {
        // Add new patient
        await apiRequest(API_ENDPOINTS.PATIENTS, {
          method: 'POST',
          body: JSON.stringify(patientData)
        })
        setSuccess('Patient created successfully')
      }
      
      // Reload patients from database
      await loadPatients()
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save patient')
      console.error('Error saving patient:', err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box>
      <PageHeader
        title="Patients"
        actionButton={{
          text: "Add Patient",
          onClick: handleOpen,
          icon: <AddIcon />
        }}
      />

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

      {/* Patients Data Grid */}
      <DataTable
        rows={patients}
        columns={columns}
        loading={loading}
        aspectRatio="16/9"
      />

      {/* Patient Form Modal */}
      <PatientForm
        open={open}
        editingPatient={editingPatient}
        onSubmit={handleSubmit}
        onClose={handleClose}
        submitting={submitting}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        open={deleteModalOpen}
        title="Confirm Delete"
        itemName={patientToDelete?.name || ''}
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
        submitting={submitting}
      />

      {/* Status Alerts */}
      <StatusAlert
        success={success}
        error={error}
        onSuccessClose={() => setSuccess(null)}
        onErrorClose={() => setError(null)}
      />
    </Box>
  )
}

export default Patients 