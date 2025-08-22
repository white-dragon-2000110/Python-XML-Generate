import React from 'react'
import { Alert, Snackbar } from '@mui/material'

interface StatusAlertProps {
  success: string | null
  error: string | null
  onSuccessClose: () => void
  onErrorClose: () => void
}

const StatusAlert: React.FC<StatusAlertProps> = ({
  success,
  error,
  onSuccessClose,
  onErrorClose
}) => {
  return (
    <>
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={onSuccessClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert onClose={onSuccessClose} severity="success">
          {success}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={onErrorClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert onClose={onErrorClose} severity="error">
          {error}
        </Alert>
      </Snackbar>
    </>
  )
}

export default StatusAlert 