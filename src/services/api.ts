// API Service - High-level API functions for the app
// Uses centralized API client for all requests
// Includes offline queue management for ride requests

import { apiGet, apiPost } from "./apiClient";
import { isBackendReachable } from "@/src/utils/connectivityHelpers";
import {
  addToQueue,
  removeFromQueue,
  incrementRetryCount,
  getPendingRequests,
  QueuedRideRequest,
} from "@/src/utils/asyncStorageQueue";
import { showToast, showSuccessToast, showErrorToast } from "@/src/utils/toastHelper";

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
};
