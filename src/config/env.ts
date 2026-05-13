/**
 * Environment Configuration - Centralized for entire app
 * Prevents hardcoding values across codebase
 */

// Auto-detect IP based on environment
const getAPIUrl = () => {
  // For development on device, use host IP
  const API_IP = "100.65.95.4";
  const API_PORT = "8000";
  return `http://${API_IP}:${API_PORT}`;
};

export const API_CONFIG = {
  // Base URL
  BASE_URL: getAPIUrl(),
  
  // API Version
  API_VERSION: "v1",
  
  // Full API endpoint prefix
  get API_PREFIX() {
    return `${this.BASE_URL}/api/${this.API_VERSION}`;
  },
  
  // Timeout settings (in ms)
  REQUEST_TIMEOUT: 15000,
  
  // Retry settings
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000, // Base delay in ms, will multiply with exponential backoff
  
  // WebSocket settings
  WEBSOCKET_URL: "ws://100.65.95.4:8000/api/v1/ws",
  WEBSOCKET_RECONNECT_INTERVAL: 5000,
  
  // Polling intervals (in ms)
  RIDE_STATUS_POLL_INTERVAL: 3000,
  DRIVER_RIDES_POLL_INTERVAL: 5000,
  ADMIN_STATS_POLL_INTERVAL: 10000,

  // Security
  ADMIN_SECRET_KEY: "malkapur_admin_secret_123",
};

/**
 * Get full endpoint URL
 */
export const getEndpointUrl = (endpoint: string): string => {
  if (endpoint.startsWith("http")) {
    return endpoint; // Already a full URL
  }
  
  // Ensure endpoint starts with /
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${API_CONFIG.API_PREFIX}${path}`;
};

/**
 * Check if API is reachable
 */
export const checkAPIHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}/api/${API_CONFIG.API_VERSION}/rides/requested`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    return response.ok;
  } catch (error) {
    return false;
  }
};
