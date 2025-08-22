import React from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  CircularProgress
} from '@mui/material'

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

interface PatientFormProps {
  open: boolean
  editingPatient: Patient | null
  onSubmit: (event: React.FormEvent) => void
  onClose: () => void
  submitting: boolean
}

const PatientForm: React.FC<PatientFormProps> = ({
  open,
  editingPatient,
  onSubmit,
  onClose,
  submitting
}) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {editingPatient ? 'Edit Patient' : 'Add New Patient'}
      </DialogTitle>
      <form onSubmit={onSubmit}>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                name="name"
                label="Full Name"
                placeholder="Enter patient's full name"
                fullWidth
                required
                defaultValue={editingPatient?.name || ''}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                name="cpf"
                label="CPF"
                placeholder="000.000.000-00"
                fullWidth
                required
                defaultValue={editingPatient?.cpf || ''}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                name="birth_date"
                label="Birth Date"
                type="date"
                fullWidth
                required
                defaultValue={editingPatient?.birth_date || ''}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                name="phone"
                label="Phone"
                placeholder="(00) 00000-0000"
                fullWidth
                required
                defaultValue={editingPatient?.phone || ''}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                name="address"
                label="Address"
                placeholder="Enter full address"
                fullWidth
                required
                defaultValue={editingPatient?.address || ''}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                name="email"
                label="Email"
                placeholder="patient@example.com"
                type="email"
                fullWidth
                required
                defaultValue={editingPatient?.email || ''}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={submitting}>Cancel</Button>
          <Button 
            type="submit" 
            variant="contained" 
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={20} /> : null}
          >
            {submitting ? 'Saving...' : (editingPatient ? 'Update' : 'Create')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  )
}

export default PatientForm 