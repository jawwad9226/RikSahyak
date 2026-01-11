// API Service - High-level API functions for the app
// Uses centralized API client for all requests
// Includes offline queue management for ride requests

import {
    QueuedRideRequest
} from "@/src/utils/asyncStorageQueue";
import { apiGet, apiPost } from "./apiClient";

// Re-export apiClient functions for convenience
export { apiGet, apiPost };

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  statusCode?: number;
}

/**
 * Callback for when a queued ride is successfully synced
 */
export type OnQueuedRideSynced = (queuedItem: QueuedRideRequest, rideResponse: any) => void;

// Store callback for queue sync events
let queueSyncCallback: OnQueuedRideSynced | null = null;

/**
 * Register callback for when queued rides are synced
 */
export function onQueuedRideSynced(callback: OnQueuedRideSynced): void {
  queueSyncCallback = callback;
}

/**
 * Calculate fare for a ride
 */
export async function calculateFare(
  pickupLocation: string,
  dropoffLocation: string,
  pickupCoords?: { latitude: number; longitude: number },
  dropoffCoords?: { latitude: number; longitude: number }
) {
  return apiPost("/rides/calculate-fare", {
    pickup_location: pickupLocation,
    dropoff_location: dropoffLocation,
    pickup_coords: pickupCoords,
    dropoff_coords: dropoffCoords,
  });
}

/**
 * Create a ride request with offline support
 * If backend reachable: POST immediately
 * If not reachable: Queue for later sync
 */
export async function createRideRequest(rideData: any): Promise<ApiResponse<any>> {
  // Check if backend is reachable
  const isOnline = await isBackendReachable();

  if (isOnline) {
    // Backend is online, create ride normally
    try {
      const response = await apiPost("/rides/request", rideData);
      return response;
    } catch (error) {
      console.error("Error creating ride request:", error);
      // If online request fails, fallback to queue
      return handleOfflineRideRequest(rideData);
    }
  } else {
    // Backend is offline, queue the request
    return handleOfflineRideRequest(rideData);
  }
}

/**
 * Handle offline ride request (queue it)
 */
async function handleOfflineRideRequest(rideData: any): Promise<ApiResponse<any>> {
  try {
    const queuedItem = await addToQueue(rideData);
    showToast("Queued (offline) — will send when online", "info");
    return {
      success: true,
      data: {
        ride_id: queuedItem.id, // Use queue ID as temporary ride ID
        status: "QUEUED",
        message: "Ride queued for offline sync",
        _queued: true, // Mark as queued for UI purposes
      },
    };
  } catch (error) {
    console.error("Error queuing ride request:", error);
    return {
      success: false,
      error: "Failed to queue ride request",
    };
  }
}

/**
 * Flush queue: attempt to sync all pending queued requests
 * Returns count of successfully synced items
 */
export async function flushQueue(): Promise<number> {
  const pending = await getPendingRequests();

  if (pending.length === 0) {
    return 0;
  }

  console.log(`[QUEUE] Flushing ${pending.length} pending requests...`);

  let successCount = 0;

  for (const queuedItem of pending) {
    try {
      // Check backend reachability before each attempt
      const isOnline = await isBackendReachable();
      if (!isOnline) {
        console.warn("[QUEUE] Backend went offline during flush, stopping");
        break;
      }

      // Try to post to backend
      const response = await apiPost("/rides/request", queuedItem.rideData);

      if (response.success && response.data) {
        // Success! Remove from queue
        await removeFromQueue(queuedItem.id);
        showSuccessToast(`Ride request synced: ${response.data.ride_id}`);
        successCount++;

        // Notify callback if registered
        if (queueSyncCallback) {
          queueSyncCallback(queuedItem, response.data);
        }
      } else {
        // API returned error (e.g., 409 Conflict)
        const errorMessage = response.error || "Unknown error";
        console.warn(`[QUEUE] Failed to sync ${queuedItem.id}: ${errorMessage}`);

        // Check if it's a 409 Conflict (passenger already has active ride)
        if (response.statusCode === 409) {
          // Mark as failed permanently
          await incrementRetryCount(queuedItem.id, errorMessage);
          showErrorToast(
            `Ride sync failed: ${errorMessage}. Manual retry available.`
          );
        } else {
          // Temporary error, increment retry
          await incrementRetryCount(queuedItem.id, errorMessage);
        }
      }
    } catch (error: any) {
      console.error(`[QUEUE] Error syncing queue item ${queuedItem.id}:`, error);
      const errorMsg = error?.message || "Network error";
      await incrementRetryCount(queuedItem.id, errorMsg);
    }
  }

  return successCount;
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
 * Get all requested rides (for drivers)
 */
export async function getRequestedRides() {
  return apiGet("/rides/requested");
}

/**
 * Get current ride for a driver
 */
export async function getDriverCurrentRide(driverId: string) {
  return apiGet(`/rides/driver/${driverId}/current`);
}

/**
 * Get current ride for a passenger
 */
export async function getPassengerCurrentRide(passengerId: string) {
  return apiGet(`/rides/passenger/${passengerId}/current`);
}

/**
 * Start a ride (IN_PROGRESS)
 */
export async function startRide(rideId: string, driverId?: string) {
  return apiPost(`/rides/${rideId}/start`, { driver_id: driverId });
}

/**
 * Complete a ride
 */
export async function completeRide(rideId: string, driverId?: string) {
  return apiPost(`/rides/${rideId}/complete`, { driver_id: driverId });
}

/**
 * Cancel a ride
 */
export async function cancelRide(rideId: string) {
  return apiPost(`/rides/${rideId}/cancel`, {});
}

/**
 * Get admin statistics
 */
export async function getAdminStats() {
  return apiGet("/admin/stats");
}

/**
 * Search locations
 */
export async function searchLocation(query: string) {
  return apiPost("/rides/search-location", { query });
}

export default {
  calculateFare,
  createRideRequest,
  acceptRide,
  getRideStatus,
  getRequestedRides,
  getDriverCurrentRide,
  getPassengerCurrentRide,
  startRide,
  completeRide,
  cancelRide,
  getAdminStats,
  searchLocation,
  flushQueue,
  onQueuedRideSynced,
};
