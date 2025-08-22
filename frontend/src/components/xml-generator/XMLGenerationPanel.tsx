import React from 'react'
import { Paper, Typography, Box, Button, FormControl, InputLabel, Select, MenuItem } from '@mui/material'
import { Code as CodeIcon, Download as DownloadIcon } from '@mui/icons-material'

interface Claim {
  id: number
  claim_number: string
  total_amount: string
}

interface XMLGenerationPanelProps {
  selectedClaimId: number | ''
  claims: Claim[]
  xmlContent: string
  isGenerating: boolean
  onClaimSelect: (claimId: number | '') => void
  onGenerate: () => void
  onDownload: () => void
}

const XMLGenerationPanel: React.FC<XMLGenerationPanelProps> = ({
  selectedClaimId,
  claims,
  xmlContent,
  isGenerating,
  onClaimSelect,
  onGenerate,
  onDownload
}) => {
  return (
    <Paper sx={{ 
      p: 4, 
      aspectRatio: '4/5',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between'
    }}>
      <Box>
        <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
          Generate XML
        </Typography>
        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>Select Claim</InputLabel>
          <Select
            value={selectedClaimId}
            label="Select Claim"
            onChange={(e) => onClaimSelect(e.target.value as number)}
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
          onClick={onGenerate}
          disabled={!selectedClaimId || isGenerating}
          sx={{ mb: 3 }}
          size="large"
        >
          Generate XML
        </Button>
      </Box>
      
      {xmlContent && (
        <Button
          fullWidth
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={onDownload}
          size="large"
        >
          Download XML
        </Button>
      )}
    </Paper>
  )
}

export default XMLGenerationPanel 