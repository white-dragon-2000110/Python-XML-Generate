// API Configuration
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000/api',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  API_KEY: 'default-secure-api-key-2024', // Add default API key
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
    
    // Handle validation errors (422 status)
    if (response.status === 422 && errorData.detail) {
      if (Array.isArray(errorData.detail)) {
        // Extract validation error messages
        const errorMessages = errorData.detail.map((error: any) => 
          `${error.loc?.join('.') || 'field'}: ${error.msg || 'Invalid value'}`
        ).join(', ')
        throw new Error(`Validation failed: ${errorMessages}`)
      } else if (typeof errorData.detail === 'string') {
        throw new Error(errorData.detail)
      }
    }
    
    // Handle other errors
    const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`
    throw new Error(errorMessage)
  }
  
  // Handle responses with no content (like DELETE operations)
  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return null
  }
  
  // Try to parse JSON, but handle cases where there's no content
  try {
    return await response.json()
  } catch (error) {
    // If JSON parsing fails and it's not a 204, it might be empty content
    if (response.status === 200 || response.status === 201) {
      return null
    }
    throw error
  }
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
        'X-API-Key': API_CONFIG.API_KEY, // Add API key header
        ...options.headers,
      },
    })
    
    return await handleApiResponse(response)
  } catch (error) {
    console.error('API request failed:', error)
    throw error
  }
} 