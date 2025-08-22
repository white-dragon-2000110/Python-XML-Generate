import React from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  CircularProgress
} from '@mui/material'

interface DeleteConfirmationModalProps {
  open: boolean
  title: string
  itemName: string
  onConfirm: () => void
  onCancel: () => void
  submitting: boolean
}

const DeleteConfirmationModal: React.FC<DeleteConfirmationModalProps> = ({
  open,
  title,
  itemName,
  onConfirm,
  onCancel,
  submitting
}) => {
  return (
    <Dialog open={open} onClose={onCancel} maxWidth="sm" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Typography>
          Are you sure you want to delete <strong>{itemName}</strong>?
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          This action cannot be undone.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} color="primary">
          Cancel
        </Button>
        <Button 
          onClick={onConfirm} 
          color="error" 
          variant="contained"
          disabled={submitting}
        >
          {submitting ? <CircularProgress size={20} /> : 'Delete'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default DeleteConfirmationModal 