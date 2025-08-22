import React from 'react'
import { Paper, Typography, Box } from '@mui/material'

interface RecentActivity {
  type: 'patient' | 'claim' | 'provider' | 'health_plan' | 'xml'
  message: string
  timestamp: string
}

interface RecentActivityProps {
  activities: RecentActivity[]
  getActivityIcon: (type: string) => React.ReactNode
  formatTimestamp: (timestamp: string) => string
}

const RecentActivity: React.FC<RecentActivityProps> = ({
  activities,
  getActivityIcon,
  formatTimestamp
}) => {
  return (
    <Paper sx={{ 
      p: 4, 
      height: '100%',
      aspectRatio: '4/3',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
        Recent Activity
      </Typography>
      <Box sx={{ 
        flex: 1,
        overflowY: 'auto',
        minHeight: 0
      }}>
        {activities.length > 0 ? (
          activities.map((activity, index) => (
            <Box key={index} display="flex" alignItems="center" mb={2} p={2} sx={{ 
              borderRadius: 1,
              '&:hover': { backgroundColor: 'rgba(0,0,0,0.02)' }
            }}>
              {getActivityIcon(activity.type)}
              <Box flex={1} ml={2}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                  {activity.message}
                </Typography>
                <Typography variant="caption" color="text.disabled">
                  {formatTimestamp(activity.timestamp)}
                </Typography>
              </Box>
            </Box>
          ))
        ) : (
          <Box textAlign="center" py={4}>
            <Typography variant="body2" color="text.secondary">
              No recent activity to display
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  )
}

export default RecentActivity 