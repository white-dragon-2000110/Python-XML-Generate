import React from 'react'
import { Box, Typography, Button } from '@mui/material'

interface PageHeaderProps {
  title: string
  actionButton?: {
    text: string
    onClick: () => void
    icon?: React.ReactNode
  }
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, actionButton }) => {
  return (
    <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
      <Typography variant="h4">{title}</Typography>
      {actionButton && (
        <Button
          variant="contained"
          startIcon={actionButton.icon}
          onClick={actionButton.onClick}
        >
          {actionButton.text}
        </Button>
      )}
    </Box>
  )
}

export default PageHeader 