import React from 'react'
import { Card, CardContent, Typography, Box } from '@mui/material'

interface StatsCardProps {
  title: string
  value: string
  icon: React.ReactNode
  color: string
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color }) => {
  return (
    <Card sx={{ 
      height: '100%',
      aspectRatio: '16/9',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center'
    }}>
      <CardContent sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        height: '100%',
        justifyContent: 'space-between'
      }}>
        <Box>
          <Typography color="text.secondary" gutterBottom variant="h6">
            {title}
          </Typography>
          <Typography variant="h4" component="div">
            {value}
          </Typography>
        </Box>
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'flex-end',
          mt: 2
        }}>
          {icon}
        </Box>
      </CardContent>
    </Card>
  )
}

export default StatsCard 