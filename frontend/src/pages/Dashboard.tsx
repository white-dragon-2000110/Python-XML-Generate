import React, { useState, useEffect } from 'react'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  CircularProgress,
  Alert,
  Button,
} from '@mui/material'
import {
  People as PeopleIcon,
  Receipt as ReceiptIcon,
  LocalHospital as LocalHospitalIcon,
  HealthAndSafety as HealthAndSafetyIcon,
  Code as CodeIcon,
  Add as AddIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material'
import { API_ENDPOINTS, apiRequest } from '../config/api'
import { useNavigate } from 'react-router-dom'

interface DashboardStats {
  totalPatients: number
  activeClaims: number
  totalProviders: number
  totalHealthPlans: number
  totalXmlFiles: number
}

interface RecentActivity {
  type: 'patient' | 'claim' | 'provider' | 'health_plan' | 'xml'
  message: string
  timestamp: string
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const [stats, setStats] = useState<DashboardStats>({
    totalPatients: 0,
    activeClaims: 0,
    totalProviders: 0,
    totalHealthPlans: 0,
    totalXmlFiles: 0,
  })
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  // Quick Actions click handlers
  const handleAddPatient = () => {
    navigate('/patients')
  }

  const handleCreateClaim = () => {
    navigate('/claims')
  }

  const handleGenerateXML = () => {
    navigate('/xml-generator')
  }

  const handleViewReports = () => {
    // For now, navigate to claims page as a placeholder for reports
    navigate('/claims')
  }

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all data in parallel
      const [patientsRes, claimsRes, providersRes, healthPlansRes] = await Promise.all([
        apiRequest(API_ENDPOINTS.PATIENTS),
        apiRequest(API_ENDPOINTS.CLAIMS),
        apiRequest(API_ENDPOINTS.PROVIDERS),
        apiRequest(API_ENDPOINTS.HEALTH_PLANS),
      ])

      // Calculate statistics
      const patients = patientsRes.items || []
      const claims = claimsRes.items || []
      const providers = providersRes.items || []
      const healthPlans = healthPlansRes.items || []

      const activeClaims = claims.filter((claim: any) => 
        claim.status === 'approved' || claim.status === 'pending'
      ).length

      setStats({
        totalPatients: patients.length,
        activeClaims,
        totalProviders: providers.length,
        totalHealthPlans: healthPlans.length,
        totalXmlFiles: 0, // Placeholder for now
      })

      // Generate recent activity from the data
      const activities: RecentActivity[] = []
      
      // Add recent patients
      const recentPatients = patients.slice(-3).reverse()
      recentPatients.forEach((patient: any) => {
        activities.push({
          type: 'patient',
          message: `New patient registered: ${patient.name}`,
          timestamp: patient.created_at || new Date().toISOString(),
        })
      })

      // Add recent claims
      const recentClaims = claims.slice(-3).reverse()
      recentClaims.forEach((claim: any) => {
        activities.push({
          type: 'claim',
          message: `Claim #${claim.claim_number} ${claim.status} for $${claim.total_amount}`,
          timestamp: claim.created_at || new Date().toISOString(),
        })
      })

      // Add recent providers
      const recentProviders = providers.slice(-2).reverse()
      recentProviders.forEach((provider: any) => {
        activities.push({
          type: 'provider',
          message: `Provider "${provider.name}" added`,
          timestamp: provider.created_at || new Date().toISOString(),
        })
      })

      // Sort activities by timestamp (most recent first)
      activities.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      
      setRecentActivity(activities.slice(0, 8)) // Show top 8 most recent activities

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
      console.error('Error loading dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'patient':
        return <PeopleIcon sx={{ fontSize: 16, color: 'primary.main', mr: 1 }} />
      case 'claim':
        return <ReceiptIcon sx={{ fontSize: 16, color: 'success.main', mr: 1 }} />
      case 'provider':
        return <LocalHospitalIcon sx={{ fontSize: 16, color: 'warning.main', mr: 1 }} />
      case 'health_plan':
        return <HealthAndSafetyIcon sx={{ fontSize: 16, color: 'info.main', mr: 1 }} />
      case 'xml':
        return <CodeIcon sx={{ fontSize: 16, color: 'secondary.main', mr: 1 }} />
      default:
        return null
    }
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
      
      if (diffInHours < 1) return 'Just now'
      if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`
      if (diffInHours < 48) return 'Yesterday'
      return date.toLocaleDateString()
    } catch {
      return 'Recently'
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={400}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    )
  }

  const statsCards = [
    {
      title: 'Total Patients',
      value: stats.totalPatients.toLocaleString(),
      icon: <PeopleIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      color: '#1976d2',
    },
    {
      title: 'Active Claims',
      value: stats.activeClaims.toLocaleString(),
      icon: <ReceiptIcon sx={{ fontSize: 40, color: 'success.main' }} />,
      color: '#2e7d32',
    },
    {
      title: 'Healthcare Providers',
      value: stats.totalProviders.toLocaleString(),
      icon: <LocalHospitalIcon sx={{ fontSize: 40, color: 'warning.main' }} />,
      color: '#ed6c02',
    },
    {
      title: 'Health Plans',
      value: stats.totalHealthPlans.toLocaleString(),
      icon: <HealthAndSafetyIcon sx={{ fontSize: 40, color: 'info.main' }} />,
      color: '#0288d1',
    }
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Welcome to the TISS Healthcare Management System. Monitor your healthcare operations and generate compliant XML files.
      </Typography>

      <Grid container spacing={4} sx={{ mb: 6 }}>
        {statsCards.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" gutterBottom variant="h6">
                      {stat.title}
                    </Typography>
                    <Typography variant="h4" component="div">
                      {stat.value}
                    </Typography>
                  </Box>
                  {stat.icon}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={4}>
        <Grid item xs={12} lg={7}>
          <Paper sx={{ p: 4, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
              Recent Activity
            </Typography>
            <Box sx={{ maxHeight: 400, overflowY: 'auto' }}>
              {recentActivity.length > 0 ? (
                recentActivity.map((activity, index) => (
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
        </Grid>

        <Grid item xs={12} lg={5}>
          <Paper sx={{ p: 4, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAddPatient}
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
                Add New Patient
              </Button>
              <Button
                variant="contained"
                startIcon={<DescriptionIcon />}
                onClick={handleCreateClaim}
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
                Create Healthcare Claim
              </Button>
              <Button
                variant="contained"
                startIcon={<CodeIcon />}
                onClick={handleGenerateXML}
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
                Generate TISS XML
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard 