import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Patients from './pages/Patients'
import Claims from './pages/Claims'
import Providers from './pages/Providers'
import HealthPlans from './pages/HealthPlans'
import XMLGenerator from './pages/XMLGenerator'

function App() {
  return (
    <Box sx={{ display: 'flex', width:'100%', height:'100%' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/patients" element={<Patients />} />
          <Route path="/claims" element={<Claims />} />
          <Route path="/providers" element={<Providers />} />
          <Route path="/health-plans" element={<HealthPlans />} />
          <Route path="/xml-generator" element={<XMLGenerator />} />
        </Routes>
      </Layout>
    </Box>
  )
}

export default App 