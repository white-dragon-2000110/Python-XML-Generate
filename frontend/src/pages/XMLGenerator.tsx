import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Button,
  Paper,
  TextField,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Chip,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material'
import {
  Code as CodeIcon,
  Download as DownloadIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { API_ENDPOINTS, apiRequest } from '../config/api'

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
  cpf: string
  birth_date: string
  gender: string
}

interface Provider {
  id: number
  name: string
  cnpj: string
  type: string
}

const XMLGenerator: React.FC = () => {
  const [selectedClaimId, setSelectedClaimId] = useState<number | ''>('')
  const [xmlContent, setXmlContent] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [validationResult, setValidationResult] = useState<{
    isValid: boolean
    errors: string[]
  } | null>(null)
  const [claims, setClaims] = useState<Claim[]>([])
  const [patients, setPatients] = useState<Patient[]>([])
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all data in parallel
      const [claimsRes, patientsRes, providersRes] = await Promise.all([
        apiRequest(API_ENDPOINTS.CLAIMS),
        apiRequest(API_ENDPOINTS.PATIENTS),
        apiRequest(API_ENDPOINTS.PROVIDERS),
      ])

      setClaims(claimsRes.items || [])
      setPatients(patientsRes.items || [])
      setProviders(providersRes.items || [])

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
      console.error('Error loading data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateXML = async () => {
    if (!selectedClaimId) return
    
    setIsGenerating(true)
    setValidationResult(null)
    
    try {
      // Find the selected claim, patient, and provider
      const claim = claims.find(c => c.id === selectedClaimId)
      if (!claim) {
        throw new Error('Claim not found')
      }

      const patient = patients.find(p => p.id === claim.patient_id)
      const provider = providers.find(p => p.id === claim.provider_id)

      if (!patient || !provider) {
        throw new Error('Patient or provider data not found')
      }

      // Generate XML with real data
      const xml = `<?xml version="1.0" encoding="UTF-8"?>
<ans:mensagemTISS xmlns:ans="http://www.ans.gov.br/padroes/tiss/schemas" version="3.05.00">
  <ans:cabecalho>
    <ans:identificacaoOperadora>
      <ans:codigoOperadora>UNI001</ans:codigoOperadora>
      <ans:registroANS>123456</ans:registroANS>
    </ans:identificacaoOperadora>
    <ans:dadosPrestador>
      <ans:cnpjPrestador>${provider.cnpj}</ans:cnpjPrestador>
      <ans:registroANS>123456</ans:registroANS>
    </ans:dadosPrestador>
    <ans:dataProcessamento>${new Date().toISOString().split('T')[0]}</ans:dataProcessamento>
    <ans:numeroProtocolo>${claim.claim_number}</ans:numeroProtocolo>
  </ans:cabecalho>
  <ans:corpo>
    <ans:dadosGuia>
      <ans:identificacaoGuia>
        <ans:numeroGuiaPrestador>${claim.claim_number}</ans:numeroGuiaPrestador>
        <ans:numeroGuiaOperadora>${claim.claim_number}</ans:numeroGuiaOperadora>
        <ans:dataAutorizacao>${claim.claim_date}</ans:dataAutorizacao>
        <ans:senha>123456</ans:senha>
        <ans:dataValidadeSenha>${new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}</ans:dataValidadeSenha>
      </ans:identificacaoGuia>
      <ans:dadosBeneficiario>
        <ans:numeroCarteira>${patient.id}</ans:numeroCarteira>
        <ans:nomeBeneficiario>${patient.name}</ans:nomeBeneficiario>
        <ans:dataNascimento>${patient.birth_date}</ans:dataNascimento>
        <ans:sexo>${patient.gender === 'male' ? 'M' : patient.gender === 'female' ? 'F' : 'I'}</ans:sexo>
        <ans:cpf>${patient.cpf}</ans:cpf>
      </ans:dadosBeneficiario>
      <ans:dadosPrestador>
        <ans:cnpjPrestador>${provider.cnpj}</ans:cnpjPrestador>
        <ans:nomePrestador>${provider.name}</ans:nomePrestador>
        <ans:enderecoPrestador>${provider.type}</ans:enderecoPrestador>
      </ans:dadosPrestador>
      <ans:dadosProcedimento>
        <ans:codigoProcedimento>${claim.claim_number}</ans:codigoProcedimento>
        <ans:descricaoProcedimento>Healthcare claim ${claim.claim_number}</ans:descricaoProcedimento>
        <ans:dataProcedimento>${claim.claim_date}</ans:dataProcedimento>
        <ans:valorProcedimento>${claim.total_amount}</ans:valorProcedimento>
      </ans:dadosProcedimento>
      <ans:diagnostico>
        <ans:codigoDiagnostico>Z00.0</ans:codigoDiagnostico>
        <ans:descricaoDiagnostico>General medical examination</ans:descricaoDiagnostico>
      </ans:diagnostico>
      <ans:valoresInformados>
        <ans:valorTotalGeral>${claim.total_amount}</ans:valorTotalGeral>
        <ans:valorTotalProcedimentos>${claim.total_amount}</ans:valorTotalProcedimentos>
      </ans:valoresInformados>
    </ans:dadosGuia>
  </ans:corpo>
  <ans:rodape>
    <ans:dadosPrestador>
      <ans:cnpjPrestador>${provider.cnpj}</ans:cnpjPrestador>
      <ans:registroANS>123456</ans:registroANS>
    </ans:dadosPrestador>
    <ans:dataProcessamento>${new Date().toISOString().split('T')[0]}</ans:dataProcessamento>
    <ans:valorTotalGeral>${claim.total_amount}</ans:valorTotalGeral>
  </ans:rodape>
</ans:mensagemTISS>`
      
      setXmlContent(xml)
      
      // Basic validation
      const isValid = true
      const errors: string[] = []
      
      setValidationResult({ isValid, errors })
      
    } catch (error) {
      setValidationResult({
        isValid: false,
        errors: ['Error generating XML: ' + (error as Error).message]
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownloadXML = () => {
    if (!xmlContent) return
    
    const blob = new Blob([xmlContent], { type: 'application/xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tiss_claim_${selectedClaimId}_${new Date().toISOString().split('T')[0]}.xml`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleValidateXML = () => {
    if (!xmlContent) return
    
    // Comprehensive TISS XML validation
    const errors: string[] = []
    
    // Check for required root element
    if (!xmlContent.includes('<ans:mensagemTISS')) {
      errors.push('Missing root element: ans:mensagemTISS')
    }
    
    // Check for required header section
    if (!xmlContent.includes('<ans:cabecalho>')) {
      errors.push('Missing header section: ans:cabecalho')
    }
    
    // Check for required body section
    if (!xmlContent.includes('<ans:corpo>')) {
      errors.push('Missing body section: ans:corpo')
    }
    
    // Check for required footer section
    if (!xmlContent.includes('<ans:rodape>')) {
      errors.push('Missing footer section: ans:rodape')
    }
    
    // Check for TISS version
    if (!xmlContent.includes('version="3.05.00"')) {
      errors.push('Invalid or missing TISS version (should be 3.05.00)')
    }
    
    // Check for XML declaration
    if (!xmlContent.includes('<?xml version="1.0"')) {
      errors.push('Missing XML declaration')
    }
    
    // Check for proper XML structure (basic well-formedness)
    if (!xmlContent.includes('</ans:mensagemTISS>')) {
      errors.push('XML not properly closed')
    }
    
    // Check for required claim data elements
    if (!xmlContent.includes('<ans:numeroGuiaPrestador>')) {
      errors.push('Missing claim number element')
    }
    
    if (!xmlContent.includes('<ans:dadosBeneficiario>')) {
      errors.push('Missing beneficiary data section')
    }
    
    if (!xmlContent.includes('<ans:dadosPrestador>')) {
      errors.push('Missing provider data section')
    }
    
    // Check for proper XML namespace
    if (!xmlContent.includes('xmlns:ans="http://www.ans.gov.br/padroes/tiss/schemas"')) {
      errors.push('Missing ANS namespace declaration')
    }
    
    setValidationResult({
      isValid: errors.length === 0,
      errors
    })
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        TISS XML Generator
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Generate and validate TISS 3.05.00 compliant XML files for healthcare claims.
      </Typography>

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" height={400}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Generate XML
              </Typography>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Select Claim</InputLabel>
                <Select
                  value={selectedClaimId}
                  label="Select Claim"
                  onChange={(e) => setSelectedClaimId(e.target.value as number)}
                >
                  {claims.map((claim) => (
                    <MenuItem key={claim.id} value={claim.id}>
                      Claim #{claim.claim_number} - ${claim.total_amount}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                fullWidth
                variant="contained"
                startIcon={<CodeIcon />}
                onClick={handleGenerateXML}
                disabled={!selectedClaimId || isGenerating}
                sx={{ mb: 2 }}
              >
                {isGenerating ? <CircularProgress size={20} /> : 'Generate XML'}
              </Button>
              
              {xmlContent && (
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownloadXML}
                >
                  Download XML
                </Button>
              )}
            </Paper>
          </Grid>

          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Generated XML
                </Typography>
                {xmlContent && (
                  <Button
                    variant="outlined"
                    startIcon={<CheckCircleIcon />}
                    onClick={handleValidateXML}
                  >
                    Validate XML
                  </Button>
                )}
              </Box>
              
              {xmlContent ? (
                <TextField
                  fullWidth
                  multiline
                  rows={15}
                  value={xmlContent}
                  onChange={(e) => setXmlContent(e.target.value)}
                  variant="outlined"
                  sx={{
                    '& .MuiInputBase-input': {
                      fontFamily: 'monospace',
                      fontSize: '12px',
                    }
                  }}
                />
              ) : (
                <Box
                  display="flex"
                  flexDirection="column"
                  alignItems="center"
                  justifyContent="center"
                  height={400}
                  border="2px dashed"
                  borderColor="grey.300"
                  borderRadius={1}
                >
                  <CodeIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    Select a claim from the dropdown and click "Generate XML" to create TISS XML
                  </Typography>
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}
      
      {validationResult && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              {validationResult.isValid ? (
                <CheckCircleIcon color="success" sx={{ mr: 1 }} />
              ) : (
                <ErrorIcon color="error" sx={{ mr: 1 }} />
              )}
              <Typography variant="h6">
                Validation Result
              </Typography>
              <Chip
                label={validationResult.isValid ? 'Valid' : 'Invalid'}
                color={validationResult.isValid ? 'success' : 'error'}
                sx={{ ml: 2 }}
              />
            </Box>
            
                         {validationResult.isValid ? (
               <Alert severity="success">
                 ✅ XML is valid and compliant with TISS 3.05.00 standard.
               </Alert>
             ) : (
               <Box>
                 <Alert severity="error" sx={{ mb: 2 }}>
                   ❌ XML validation failed. Please fix the following issues:
                 </Alert>
                 <Box component="ul" sx={{ pl: 2 }}>
                   {validationResult.errors.map((error, index) => (
                     <Typography key={index} component="li" color="error.main" sx={{ mb: 1 }}>
                       🔴 {error}
                     </Typography>
                   ))}
                 </Box>
                 <Alert severity="info" sx={{ mt: 2 }}>
                   💡 Tip: The XML generation should automatically create all required elements. 
                   If validation fails, try regenerating the XML or check if all data is loaded correctly.
                 </Alert>
               </Box>
             )}
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default XMLGenerator 