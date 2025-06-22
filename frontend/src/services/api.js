const API_BASE = '/admin/api'

// Helper function for API calls
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  
  const config = {
    credentials: 'include', // Include cookies for session auth
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  const response = await fetch(url, config)
  
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`
    
    try {
      const errorData = await response.json()
      
      if (errorData.detail) {
        // Check if detail is an array (FastAPI validation errors)
        if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map(err => err.msg || err.message || err).join(', ')
        } else {
          errorMessage = errorData.detail
        }
      } else if (errorData.message) {
        errorMessage = errorData.message
      } else if (Array.isArray(errorData)) {
        // Handle validation errors array
        errorMessage = errorData.map(err => err.msg || err.message || err).join(', ')
      }
    } catch (e) {
      errorMessage = `HTTP ${response.status}`
    }
    
    throw new Error(errorMessage)
  }

  return response.json()
}

// Auth API
export const auth = {
  login: (username, password) => 
    apiCall('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  
  logout: () => 
    apiCall('/auth/logout', { method: 'POST' }),
  
  status: () => 
    apiCall('/auth/status'),
}

// Dashboard API
export const dashboard = {
  get: () => apiCall('/dashboard'),
}

// Clients API
export const clients = {
  list: () => apiCall('/clients'),
  
  get: (clientId) => apiCall(`/clients/${clientId}`),
  
  create: (data) =>
    apiCall('/clients', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (clientId, data) =>
    apiCall(`/clients/${clientId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  delete: (clientId) =>
    apiCall(`/clients/${clientId}`, { method: 'DELETE' }),
}

// API Keys API
export const apiKeys = {
  create: (clientId, data) =>
    apiCall(`/clients/${clientId}/keys`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  delete: (keyValue) =>
    apiCall(`/keys/${keyValue}`, { method: 'DELETE' }),
}

// Tools API
export const tools = {
  configure: (clientId, toolName, configuration) =>
    apiCall(`/clients/${clientId}/tools/${toolName}`, {
      method: 'POST',
      body: JSON.stringify({ configuration }),
    }),
  
  delete: (clientId, toolName) =>
    apiCall(`/clients/${clientId}/tools/${toolName}`, { method: 'DELETE' }),
}

// Resources API
export const resources = {
  configure: (clientId, resourceName, configuration) =>
    apiCall(`/clients/${clientId}/resources/${resourceName}`, {
      method: 'POST',
      body: JSON.stringify({ configuration }),
    }),
  
  delete: (clientId, resourceName) =>
    apiCall(`/clients/${clientId}/resources/${resourceName}`, { method: 'DELETE' }),
}

// Tool Calls Analytics API
export const toolCalls = {
  list: (params = {}) => {
    const searchParams = new URLSearchParams()
    
    // Add parameters if provided
    if (params.client_id) searchParams.append('client_id', params.client_id)
    if (params.tool_name) searchParams.append('tool_name', params.tool_name)
    if (params.search) searchParams.append('search', params.search)
    if (params.limit) searchParams.append('limit', params.limit.toString())
    if (params.offset) searchParams.append('offset', params.offset.toString())
    if (params.order_by) searchParams.append('order_by', params.order_by)
    if (params.order_dir) searchParams.append('order_dir', params.order_dir)
    
    const query = searchParams.toString()
    return apiCall(`/tool-calls${query ? '?' + query : ''}`)
  },

  stats: (params = {}) => {
    const searchParams = new URLSearchParams()
    
    if (params.client_id) searchParams.append('client_id', params.client_id)
    if (params.days) searchParams.append('days', params.days.toString())
    
    const query = searchParams.toString()
    return apiCall(`/tool-calls/stats${query ? '?' + query : ''}`)
  },

  listForClient: (clientId, params = {}) => {
    const searchParams = new URLSearchParams()
    
    if (params.tool_name) searchParams.append('tool_name', params.tool_name)
    if (params.search) searchParams.append('search', params.search)
    if (params.limit) searchParams.append('limit', params.limit.toString())
    if (params.offset) searchParams.append('offset', params.offset.toString())
    if (params.order_by) searchParams.append('order_by', params.order_by)
    if (params.order_dir) searchParams.append('order_dir', params.order_dir)
    
    const query = searchParams.toString()
    return apiCall(`/clients/${clientId}/tool-calls${query ? '?' + query : ''}`)
  },

  statsForClient: (clientId, params = {}) => {
    const searchParams = new URLSearchParams()
    
    if (params.days) searchParams.append('days', params.days.toString())
    
    const query = searchParams.toString()
    return apiCall(`/clients/${clientId}/tool-calls/stats${query ? '?' + query : ''}`)
  },
}

// Admin Management API
export const admins = {
  list: () => apiCall('/admins'),
  
  create: (data) =>
    apiCall('/admins', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  delete: (username) =>
    apiCall(`/admins/${username}`, { method: 'DELETE' }),
  
  changePassword: (username, newPassword) =>
    apiCall(`/admins/${username}/change-password`, {
      method: 'POST',
      body: JSON.stringify({ new_password: newPassword }),
    }),
}

// System Prompts API
export const systemPrompts = {
  list: (clientId) => 
    apiCall(`/clients/${clientId}/prompts`),
  
  generate: (clientId, data) =>
    apiCall(`/clients/${clientId}/prompts/generate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  save: (clientId, data) =>
    apiCall(`/clients/${clientId}/prompts`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  get: (promptId) =>
    apiCall(`/prompts/${promptId}`),
  
  setActive: (clientId, promptId) =>
    apiCall(`/clients/${clientId}/prompts/active/${promptId}`, {
      method: 'PUT',
    }),
}