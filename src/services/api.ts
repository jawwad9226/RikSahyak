// API Configuration and Utility Functions

const API_BASE_URL = "http://192.168.1.5:8000"; // Change to your laptop's LAN IP
const API_VERSION = "v1";

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Make a GET request to the backend
 */
export async function apiGet<T>(endpoint: string): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/${API_VERSION}${endpoint}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();
    return { success: response.ok, data };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}

/**
 * Make a POST request to the backend
 */
export async function apiPost<T>(
  endpoint: string,
  body: any
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/${API_VERSION}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return { success: response.ok, data };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}

/**
 * Calculate fare for a ride
 */
export async function calculateFare(pickupLocation: string, dropoffLocation: string) {
  return apiPost("/rides/calculate-fare", {
    pickup_location: pickupLocation,
    dropoff_location: dropoffLocation,
  });
}

/**
 * Create a ride request
 */
export async function createRideRequest(rideData: any) {
  return apiPost("/rides/request", rideData);
}

/**
 * Accept a ride (for drivers)
 */
export async function acceptRide(rideId: string, driverId: string) {
  return apiPost("/rides/accept", {
    ride_id: rideId,
    driver_id: driverId,
  });
}

/**
 * Get ride status
 */
export async function getRideStatus(rideId: string) {
  return apiGet(`/rides/status/${rideId}`);
}

/**
 * Connect to WebSocket for real-time updates
 */
export function connectWebSocket(userId: string, onMessage: (data: any) => void) {
  const wsUrl = `ws://192.168.1.5:8000/api/v1/ws/rides/${userId}`;
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };

  return ws;
}

export default {
  apiGet,
  apiPost,
  calculateFare,
  createRideRequest,
  acceptRide,
  getRideStatus,
  connectWebSocket,
};
