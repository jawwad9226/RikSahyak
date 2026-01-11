# Offline Queue & Auto-Sync - Quick Reference

## What Was Implemented

Complete offline-first ride booking system with automatic background sync.

- **Offline Support**: Queue requests when backend unreachable
- **Auto-Sync**: FIFO sync on app start & online event
- **UI Feedback**: Queue indicator, manual retry, status badges
- **Error Handling**: Retry logic (max 3), 409 conflict handling
- **Navigation**: Auto-navigate to active ride when synced

## Files Created/Modified

| File | Type | Changes |
|------|------|---------|
| `src/utils/asyncStorageQueue.ts` | NEW | Queue management API |
| `src/utils/toastHelper.ts` | NEW | Notifications |
| `src/utils/connectivityHelpers.ts` | NEW | Health checks |
| `src/services/api.ts` | MOD | Offline-aware endpoints |
| `src/context/UserContext.tsx` | MOD | Auto-sync on startup |
| `app/passenger/home.tsx` | MOD | Queue UI & callbacks |

## Core Functions

### Queue Operations
```typescript
// Add to queue (when offline)
addToQueue(rideData) → QueuedRideRequest

// Get pending requests
getPendingRequests() → QueuedRideRequest[]

// Sync all pending (FIFO)
flushQueue() → number (synced count)

// Reset for manual retry
resetRetryCount(queueId) → QueuedRideRequest

// Get statistics
getQueueStats() → {total, pending, failed, maxRetries}
```

### Connectivity
```typescript
// Check backend availability (2s timeout)
isBackendReachable() → boolean

// Listen for online/offline events
setupConnectivityListener(onOnline, onOffline) → cleanup
```

### Notifications
```typescript
// Show toast messages
showToast(message, type: "success"|"error"|"info")
showSuccessToast(message)
showErrorToast(message)
```

## User Flow

### When Offline
1. User books ride
2. Backend check fails → Queue request
3. Shows: "Queued (offline) — will send when online"
4. Queue indicator shows count

### When Online
1. App detects online (start or event)
2. Auto-syncs queue (FIFO)
3. Shows: "Ride request synced: RIDE-0001" (toast)
4. Auto-navigates to active ride

### Manual Retry
1. User sees "X Ride Request(s) Queued"
2. Taps "Retry" button
3. Forces sync attempt immediately

## Queue States

```
PENDING      → Ready to sync (retryCount < 3)
FAILED       → Exhausted retries OR 409 conflict
SYNCED       → Removed from queue (success)
```

## Retry Logic

| Attempt | Error Type | Action |
|---------|-----------|--------|
| 1 | Network | Retry (count=1) |
| 2 | Network | Retry (count=2) |
| 3 | Network | Fail (count=3) |
| Any | 409 Conflict | Fail immediately |

**Note**: 409 fails immediately (passenger already has active ride)

## UI Components

### Queue Indicator
```
📋 1 Ride Request(s) Queued
   Offline — waiting for connection
   [Retry]
```

**Location**: Below ride status on passenger home

### Status Badge
```
Queued (offline) — will send when online
```

**Location**: Ride status section when `rideStatus === "QUEUED"`

### Notifications
```
On Queue: "Queued (offline) — will send when online" (info)
On Sync: "Ride request synced: RIDE-0001" (success)
On Fail: "Ride sync failed: ... Manual retry available." (error)
```

## AsyncStorage Key

```
riksahyak:queuedRequests
```

Structure:
```json
{
  "requests": [
    {
      "id": "queue-1704967200000-abc123",
      "rideData": {...},
      "createdAt": 1704967200000,
      "retryCount": 0,
      "status": "pending",
      "error": null
    }
  ]
}
```

## Health Check

**Endpoint**: `GET /health`
**Timeout**: 2 seconds
**Success**: Any 2xx response
**Used by**: `isBackendReachable()`

## Event Triggers

| Event | Action |
|-------|--------|
| App Start | `flushQueue()` |
| Online Event | `flushQueue()` |
| Manual Retry | `handleRetryQueue()` → `flushQueue()` |
| Queued Ride Synced | Auto-navigate via callback |

## Configuration

```typescript
// Max retry attempts per item
const MAX_RETRIES = 3;

// Health check timeout
const HEALTH_CHECK_TIMEOUT = 2000; // ms

// Queue key
const QUEUE_KEY = "riksahyak:queuedRequests";
```

## Testing

### Test Offline Booking
1. Disconnect network (airplane mode)
2. Calculate fare & book ride
3. See: "Queued (offline)"
4. Reconnect
5. See: Success toast & auto-navigate

### Test Multiple Bookings
1. Create 3 rides offline
2. See: Queue indicator "3 Queued"
3. Reconnect
4. See: All 3 synced sequentially

### Test 409 Conflict
1. Create ride offline
2. Reconnect with existing active ride
3. See: "Sync failed: already has active ride"
4. Tap Retry after resolving conflict

### Test Manual Retry
1. Force sync fail (use dev tools)
2. Item marked failed (retryCount=3)
3. Tap "Retry" button
4. Item reset (retryCount=0)
5. Syncs again

## Deployment Notes

- ✅ Offline queueing works
- ✅ Auto-sync on startup
- ✅ Online/offline detection
- ✅ FIFO order maintained
- ✅ Retry logic (max 3)
- ✅ 409 handling
- ✅ Manual retry UI
- ✅ Notifications
- ✅ Auto-navigation
- ✅ Error logging

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Queue not syncing | Check: `/health` endpoint exists, network connectivity |
| Manual retry stuck | Clear queue: `AsyncStorage.removeItem('riksahyak:queuedRequests')` |
| Toast not showing | Ensure Alert dialog is properly dismissed |
| Auto-navigate failing | Check ride polling interval (default 2s) |
| Queue indicator not showing | Verify `queueCount` state updates on focus |

---

**Status**: ✅ Production Ready
**Commit**: `e0150bb`
**Date**: 2026-01-11
