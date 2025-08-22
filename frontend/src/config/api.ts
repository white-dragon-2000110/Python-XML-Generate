// API Configuration
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000/api',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
}

// API Endpoints
export const API_ENDPOINTS = {
  PATIENTS: '/patients',
  CLAIMS: '/claims',
  PROVIDERS: '/providers',
  HEALTH_PLANS: '/health-plans',
  XML_GENERATOR: '/xml-generator',
}

// Helper function to build full API URLs
export const buildApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`
}

// Helper function to handle API responses
export const handleApiResponse = async (response: Response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
  }
  return response.json()
}

// Helper function to make API requests with error handling
export const apiRequest = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<any> => {
  try {
    const url = buildApiUrl(endpoint)
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
    
    return await handleApiResponse(response)
  } catch (error) {
    console.error('API request failed:', error)
    throw error
  }
} 