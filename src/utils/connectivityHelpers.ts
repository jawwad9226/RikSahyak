/**
 * Connectivity Detection Utilities
 * Checks if backend is reachable using health endpoint
 */

import { API_CONFIG, getEndpointUrl } from "@/src/config/env";

/**
 * Check if backend is reachable with timeout
 * Uses GET /health endpoint with 2s timeout
 */
export async function isBackendReachable(): Promise<boolean> {
  try {
    const healthUrl = getEndpointUrl("/health");
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout

    const response = await fetch(healthUrl, {
      method: "GET",
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    
    // Success if we get any 2xx response
    return response.ok;
  } catch (error) {
    console.warn("Backend health check failed:", error);
    return false;
  }
}

/**
 * Setup online/offline event listeners
 * Returns cleanup function
 */
export function setupConnectivityListener(onOnline: () => void, onOffline: () => void): () => void {
  if (typeof window !== "undefined") {
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);

    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }

  return () => {};
}
