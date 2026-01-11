/**
 * Offline Queue Management for Ride Requests
 * Stores ride requests in AsyncStorage and manages retry logic
 */

import AsyncStorage from "@react-native-async-storage/async-storage";

export interface QueuedRideRequest {
  id: string; // Unique queue item ID
  rideData: any; // Full ride payload
  createdAt: number; // Timestamp
  retryCount: number; // Current retry count (0-3)
  status: "pending" | "failed"; // pending or failed
  error?: string; // Last error message
}

export interface QueueState {
  requests: QueuedRideRequest[];
  lastSyncAttempt?: number;
}

const QUEUE_KEY = "riksahyak:queuedRequests";
const MAX_RETRIES = 3;

/**
 * Generate unique queue item ID
 */
function generateQueueId(): string {
  return `queue-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Get current queue state from AsyncStorage
 */
export async function getQueueState(): Promise<QueueState> {
  try {
    const stored = await AsyncStorage.getItem(QUEUE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (e) {
    console.error("Failed to read queue state:", e);
  }
  return { requests: [] };
}

/**
 * Save queue state to AsyncStorage
 */
async function saveQueueState(state: QueueState): Promise<void> {
  try {
    await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(state));
  } catch (e) {
    console.error("Failed to save queue state:", e);
    throw e;
  }
}

/**
 * Add a ride request to the queue
 */
export async function addToQueue(rideData: any): Promise<QueuedRideRequest> {
  const state = await getQueueState();
  const queuedItem: QueuedRideRequest = {
    id: generateQueueId(),
    rideData,
    createdAt: Date.now(),
    retryCount: 0,
    status: "pending",
  };

  state.requests.push(queuedItem);
  await saveQueueState(state);
  return queuedItem;
}

/**
 * Get all pending queue items
 */
export async function getPendingRequests(): Promise<QueuedRideRequest[]> {
  const state = await getQueueState();
  return state.requests.filter((r) => r.status === "pending" && r.retryCount < MAX_RETRIES);
}

/**
 * Get all failed queue items
 */
export async function getFailedRequests(): Promise<QueuedRideRequest[]> {
  const state = await getQueueState();
  return state.requests.filter((r) => r.status === "failed" || r.retryCount >= MAX_RETRIES);
}

/**
 * Get all queued requests (pending + failed)
 */
export async function getAllQueuedRequests(): Promise<QueuedRideRequest[]> {
  const state = await getQueueState();
  return state.requests;
}

/**
 * Get count of all queued requests
 */
export async function getQueueCount(): Promise<number> {
  const state = await getQueueState();
  return state.requests.length;
}

/**
 * Update retry count for a queue item
 */
export async function incrementRetryCount(
  queueId: string,
  error?: string
): Promise<QueuedRideRequest | null> {
  const state = await getQueueState();
  const item = state.requests.find((r) => r.id === queueId);

  if (!item) {
    console.warn(`Queue item ${queueId} not found`);
    return null;
  }

  item.retryCount += 1;
  if (error) {
    item.error = error;
  }

  // Mark as failed if max retries exceeded
  if (item.retryCount >= MAX_RETRIES) {
    item.status = "failed";
  }

  await saveQueueState(state);
  return item;
}

/**
 * Mark a queue item as succeeded and remove it
 */
export async function removeFromQueue(queueId: string): Promise<void> {
  const state = await getQueueState();
  state.requests = state.requests.filter((r) => r.id !== queueId);
  await saveQueueState(state);
}

/**
 * Reset retry count for a failed item (for manual retry)
 */
export async function resetRetryCount(queueId: string): Promise<QueuedRideRequest | null> {
  const state = await getQueueState();
  const item = state.requests.find((r) => r.id === queueId);

  if (!item) {
    return null;
  }

  item.retryCount = 0;
  item.status = "pending";
  item.error = undefined;
  await saveQueueState(state);
  return item;
}

/**
 * Clear entire queue
 */
export async function clearQueue(): Promise<void> {
  try {
    await AsyncStorage.removeItem(QUEUE_KEY);
  } catch (e) {
    console.error("Failed to clear queue:", e);
    throw e;
  }
}

/**
 * Get queue statistics
 */
export async function getQueueStats(): Promise<{
  total: number;
  pending: number;
  failed: number;
  maxRetries: number;
}> {
  const state = await getQueueState();
  const pending = state.requests.filter((r) => r.status === "pending" && r.retryCount < MAX_RETRIES)
    .length;
  const failed = state.requests.filter((r) => r.status === "failed" || r.retryCount >= MAX_RETRIES)
    .length;

  return {
    total: state.requests.length,
    pending,
    failed,
    maxRetries: MAX_RETRIES,
  };
}
