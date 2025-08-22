import React from 'react'
import { Paper, Typography, Box, Button } from '@mui/material'

interface QuickActionsProps {
  actions: Array<{
    text: string
    onClick: () => void
    icon: React.ReactNode
  }>
}

const QuickActions: React.FC<QuickActionsProps> = ({ actions }) => {
  return (
    <Paper sx={{ 
      p: 4, 
      height: '100%',
      aspectRatio: '4/3',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
        Quick Actions
      </Typography>
      <Box sx={{ 
        flex: 1,
        display: 'flex', 
        flexDirection: 'column', 
        gap: 2.5,
        justifyContent: 'center'
      }}>
        {actions.map((action, index) => (
          <Button
            key={index}
            variant="contained"
            startIcon={action.icon}
            onClick={action.onClick}
            fullWidth
            size="large"
            sx={{ 
              justifyContent: 'flex-start', 
              textTransform: 'none',
              py: 1.5,
              px: 3,
              borderRadius: 2
            }}
          >
            {action.text}
          </Button>
        ))}
      </Box>
    </Paper>
  )
}

export default QuickActions 