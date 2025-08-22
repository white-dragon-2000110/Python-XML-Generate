import React from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  MenuItem,
  FormControl,
  InputLabel,
  Select
} from '@mui/material'

interface Claim {
  id: number
  patient_id: number
  provider_id: number
  claim_number: string
  claim_date: string
  total_amount: string
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

interface ClaimFormProps {
  open: boolean
  editingClaim: Claim | null
  patients: Patient[]
  providers: Provider[]
  onSubmit: (event: React.FormEvent) => void
  onClose: () => void
}

const ClaimForm: React.FC<ClaimFormProps> = ({
  open,
  editingClaim,
  patients,
  providers,
  onSubmit,
  onClose
}) => {
  const statusOptions = ['pending', 'approved', 'denied', 'paid']

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {editingClaim ? 'Edit Claim' : 'Add New Claim'}
      </DialogTitle>
      <form onSubmit={onSubmit}>
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
                name="claim_number"
                label="Claim Number"
                placeholder="Enter claim number"
                fullWidth
                required
                defaultValue={editingClaim?.claim_number || ''}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                name="total_amount"
                label="Total Amount"
                placeholder="0.00"
                type="number"
                fullWidth
                required
                defaultValue={editingClaim?.total_amount || ''}
                inputProps={{ step: 0.01, min: 0 }}
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
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained">
            {editingClaim ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  )
}

export default ClaimForm 