// Configuration for different environments
const config = {
  // Backend URL for MCP endpoints
  // In development, we need to use the backend port (8000)
  // In production, both frontend and backend are served from the same origin
  getBackendUrl: () => {
    // Check if we have an explicit backend URL set via environment variable
    if (import.meta.env.VITE_BACKEND_URL) {
      return import.meta.env.VITE_BACKEND_URL
    }
    
    // In development, detect localhost and switch to backend port
    if (import.meta.env.DEV && window.location.hostname === 'localhost') {
      return `${window.location.protocol}//${window.location.hostname}:8000`
    }
    
    // In production or other cases, use same origin
    return window.location.origin
  },
  
  // Get the MCP URL for a given API key
  getMcpUrl: (keyValue) => {
    return `${config.getBackendUrl()}/mcp/${keyValue}`
  }
}

export default config 