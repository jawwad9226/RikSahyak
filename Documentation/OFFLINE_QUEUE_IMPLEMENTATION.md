# Offline Queue & Auto-Sync Implementation

**Commit**: `e0150bb - frontend: add offline queue and auto-sync for ride requests`

## Overview

Full offline-first booking queue with background sync. Ride requests are automatically queued when backend is unreachable and synced when connection is restored.

---

## Architecture

### Components

#### 1. **Queue Storage** (`src/utils/asyncStorageQueue.ts`)
- Persists ride requests to AsyncStorage with key: `riksahyak:queuedRequests`
- Tracks retry count (max 3) and failure status per item
- Queue item structure:
  ```typescript
  {
    id: string;           // Unique queue ID
    rideData: any;        // Full ride request payload
    createdAt: number;    // Timestamp
    retryCount: number;   // 0-3
    status: "pending" | "failed";
    error?: string;       // Last error message
  }
  ```

#### 2. **Connectivity Detection** (`src/utils/connectivityHelpers.ts`)
- Health check endpoint: `GET /health` with 2s timeout
- `isBackendReachable()` - Probes backend availability
- `setupConnectivityListener()` - Listens to online/offline events

#### 3. **Notifications** (`src/utils/toastHelper.ts`)
- Simple toast/alert wrapper for user feedback
- Types: success, error, info
- Shows meaningful messages about queue status

#### 4. **API Layer** (`src/services/api.ts`)
- `createRideRequest()` - Smart endpoint (online/offline)
- `flushQueue()` - FIFO sync of pending requests
- `onQueuedRideSynced()` - Callback when queued ride is synced

#### 5. **Context & Auto-Sync** (`src/context/UserContext.tsx`)
- Auto-flush queue on app start
- Setup online/offline listeners
- Track synced ride IDs for navigation

#### 6. **UI Integration** (`app/passenger/home.tsx`)
- Queue indicator badge (when items queued)
- Manual retry button
- Shows "Queued (offline)" status
- Auto-navigate to active ride when synced

---

## User Flow

### Normal (Online) Flow
1. User taps "Book Ride"
2. Backend reachable check passes
3. POST `/rides/request` sent immediately
4. Success → navigate to active ride
5. Error (409) → show error message

### Offline Flow
1. User taps "Book Ride"
2. Backend reachable check fails (timeout/no response)
3. Ride queued to AsyncStorage
4. UI shows: "Queued (offline) — will send when online"
5. Queue indicator shows: "1 Ride Request(s) Queued"

### Auto-Sync Flow (Background)
1. **App Start** → `flushQueue()` called automatically
2. **Online Event** → `flushQueue()` called when connection restored
3. For each pending item:
   - Check backend reachable
   - POST to `/rides/request`
   - On success: Remove from queue, show toast, auto-navigate
   - On 409 conflict: Mark failed (passenger already has active ride)
   - On other error: Increment retry count
4. **Max Retries (3)** → Mark item "failed", show manual retry button

### Manual Retry Flow
1. User sees queue indicator with "Retry" button
2. User taps "Retry"
3. `handleRetryQueue()` → `flushQueue()`
4. Same as auto-sync: attempt to send all pending

---

## Queue Lifecycle

### States & Transitions

```
CREATED (retryCount=0, status=pending)
    ↓ (on app start / online event)
SEND ATTEMPT #1
    ├─ Success → REMOVED (from queue)
    ├─ 409 → FAILED (passenger already has active)
    └─ Network error → RETRY (retryCount=1)
        ↓
SEND ATTEMPT #2
    ├─ Success → REMOVED
    ├─ 409 → FAILED
    └─ Network error → RETRY (retryCount=2)
        ↓
SEND ATTEMPT #3
    ├─ Success → REMOVED
    ├─ 409 → FAILED
    └─ Network error → FAILED (retryCount=3)
        ↓
MANUAL RETRY (user taps Retry button)
    ├─ resetRetryCount() → retryCount=0, status=pending
    ├─ flushQueue() → attempt to send again
```

### Queue Statistics

```typescript
{
  total: 5,          // All items (pending + failed)
  pending: 3,        // Ready to send (retryCount < 3)
  failed: 2,         // Exhausted retries or 409
  maxRetries: 3      // Constant
}
```

---

## API Functions

### Queue Management

**`getQueueState(): Promise<QueueState>`**
- Get current queue state from AsyncStorage

**`addToQueue(rideData): Promise<QueuedRideRequest>`**
- Add new ride to queue
- Returns queue item with ID and metadata

**`getPendingRequests(): Promise<QueuedRideRequest[]>`**
- Get all items ready to sync (retryCount < 3)

**`getFailedRequests(): Promise<QueuedRideRequest[]>`**
- Get all failed items (exhausted retries or 409)

**`getAllQueuedRequests(): Promise<QueuedRideRequest[]>`**
- Get all queued items (pending + failed)

**`getQueueCount(): Promise<number>`**
- Get total count of all queued items

**`incrementRetryCount(queueId, error): Promise<QueuedRideRequest | null>`**
- Increment retry count for an item
- Mark as "failed" if maxRetries exceeded

**`removeFromQueue(queueId): Promise<void>`**
- Remove successfully synced item from queue

**`resetRetryCount(queueId): Promise<QueuedRideRequest | null>`**
- Reset retry count to 0 for manual retry

**`getQueueStats(): Promise<{total, pending, failed, maxRetries}>`**
- Get queue statistics

### Ride API (Offline-Aware)

**`createRideRequest(rideData): Promise<ApiResponse>`**
- Smart endpoint that checks backend availability
- Online: POST immediately
- Offline: Queue and return temporary ride_id (queue ID)
- Response includes `_queued: true` flag for UI

**`flushQueue(): Promise<number>`**
- Sync all pending queued requests FIFO
- Returns count of successfully synced items
- On success for each: Remove, notify user, callback

**`onQueuedRideSynced(callback): void`**
- Register callback for when queued ride is synced
- Callback receives: `(queuedItem, rideResponse)`
- Used to trigger navigation to active ride

---

## Connectivity Detection

### Health Check

```typescript
isBackendReachable(): Promise<boolean>
```

- Endpoint: `GET /health` (must be implemented on backend)
- Timeout: 2 seconds
- Success: Any 2xx response
- Failure: Timeout, network error, non-2xx response

### Event Listeners

```typescript
setupConnectivityListener(onOnline, onOffline): () => void
```

- Listens to `online` and `offline` events
- Calls `onOnline()` when device comes online
- Calls `onOffline()` when device goes offline
- Returns cleanup function to remove listeners

---

## UI Components

### Queue Indicator

**Location**: Passenger home screen (below ride status)
**Shown when**: `queueCount > 0`
**Content**:
- 📋 Icon
- Count: "X Ride Request(s) Queued"
- Subtitle: "Offline — waiting for connection"
- Retry button

**Styling**:
- Background: `#FFF3CD` (light yellow)
- Border: `#FFD700` (gold)
- Button: Gold with dark text

### Status Badge

**Location**: Ride status section
**Shown when**: `rideStatus === "QUEUED"`
**Text**: "Queued (offline) — will send when online"
**Context**: Displayed when ride request is queued

### Toast Notifications

**On Queue Add**:
```
"Queued (offline) — will send when online" (info)
```

**On Successful Sync**:
```
"Ride request synced: RIDE-0001" (success)
```

**On Sync Failure (409)**:
```
"Ride sync failed: Passenger already has an active ride. Manual retry available." (error)
```

---

## State Management

### UserContext Updates

```typescript
interface UserContextType {
  ...existing
  queuedRideId?: string;              // When queued ride synced
  setQueuedRideId: (id?: string) => void;
}
```

**On app start**:
1. Load user
2. Call `flushQueue()`
3. Setup connectivity listeners
4. Register sync callback

**On reconnect**:
1. `flushQueue()` called
2. Synced ride ID passed to callback
3. Callback sets `queuedRideId`

**On component mount** (`useFocusEffect`):
1. Get queue stats
2. Update `queueCount` state

**Navigation**:
```typescript
useEffect(() => {
  if (queuedRideId) {
    // Set ride ID and start polling
    // Will auto-navigate when ride is assigned
  }
}, [queuedRideId])
```

---

## Error Handling

### Retry Logic

**Network Errors** (0-2 retries):
- Increment retry count
- Keep status as "pending"
- Will retry on next sync attempt

**409 Conflict Errors** (immediate fail):
- Error: Passenger already has active ride
- Mark as "failed" immediately
- Show: "Manual retry available"
- Reason: 409 indicates business logic violation

**Other API Errors**:
- Same as network errors: retry up to 3 times

### Manual Recovery

**Failed Items**:
1. User sees queue indicator
2. Taps "Retry" button
3. `resetRetryCount(queueId)` → retryCount=0
4. Status changed back to "pending"
5. `flushQueue()` attempts again

---

## Implementation Details

### AsyncStorage Key Structure

```
riksahyak:queuedRequests
{
  requests: [
    {
      id: "queue-1704967200000-abc123def",
      rideData: {...},
      createdAt: 1704967200000,
      retryCount: 0,
      status: "pending"
    }
  ],
  lastSyncAttempt?: 1704967300000
}
```

### Timing & Throttling

- **App Start Flush**: No delay (immediate)
- **Online Event Flush**: No delay (immediate)
- **Manual Retry**: No delay (immediate)
- **Health Check Timeout**: 2 seconds
- **Polling Interval**: 2 seconds (for ride status)

### Concurrency & Race Conditions

- Queue operations use AsyncStorage's built-in atomicity
- Each sync attempt reads latest state before posting
- On success: immediately removes from queue
- On failure: updates retry count with error details
- Thread-safe for multiple sync attempts

---

## Testing Scenarios

### Scenario 1: Offline Booking
1. Toggle airplane mode or disconnect network
2. Calculate fare
3. Tap "Book Ride"
4. See: "Queued (offline) — will send when online"
5. See queue indicator with count
6. Reconnect network
7. See: "Ride request synced: RIDE-0001" (toast)
8. Auto-navigate to active ride

### Scenario 2: Multiple Offline Bookings
1. Disconnect network
2. Create 3 ride requests
3. See: Queue indicator "3 Ride Request(s) Queued"
4. Each shows "QUEUED" status
5. Reconnect network
6. See: All 3 synced sequentially (FIFO)
7. 3 success toasts appear
8. Navigate to last ride

### Scenario 3: Failed Request (409 Conflict)
1. Disconnect network, create ride
2. Reconnect
3. Queue syncs, but passenger already has active ride
4. See: "Ride sync failed: ... Manual retry available."
5. Wait for next auto-sync or tap Retry
6. If passenger no longer has active: Syncs successfully

### Scenario 4: Manual Retry After Failure
1. Queue item fails (retryCount=3)
2. Tap "Retry" button
3. Queue item reset (retryCount=0, status=pending)
4. `flushQueue()` attempts again
5. Success or failure based on current state

### Scenario 5: App Restart
1. Create offline ride requests
2. Force quit app
3. Reopen app
4. Auto-sync on startup
5. See: "Ride request synced: RIDE-0002" (toast)
6. Auto-navigate if ride is assigned

---

## Files Modified/Created

| File | Changes | Purpose |
|------|---------|---------|
| `src/utils/asyncStorageQueue.ts` | NEW (+175 lines) | Queue persistence & management |
| `src/utils/toastHelper.ts` | NEW (+38 lines) | User notifications |
| `src/utils/connectivityHelpers.ts` | NEW (+28 lines) | Backend health checks |
| `src/services/api.ts` | +125 lines | Queue-aware API & sync |
| `src/context/UserContext.tsx` | +43 lines | Auto-sync on startup |
| `app/passenger/home.tsx` | +133 lines | Queue UI & callbacks |

**Total**: 542 lines of code, 6 files touched

---

## Future Enhancements

1. **Persistent Ride ID Mapping**: Store ride ID mapping when synced
2. **Retry Backoff**: Implement exponential backoff for retries
3. **Queue Encryption**: Encrypt sensitive ride data in AsyncStorage
4. **Analytics**: Log queue stats and sync success rates
5. **User Preferences**: Settings for auto-sync behavior
6. **Batch Sync**: Group multiple requests in single transaction
7. **Network Type Detection**: Different behavior for wifi/cellular
8. **Queue Priority**: Prioritize older requests over newer ones

---

## Deployment Checklist

- ✅ Queue persistence works offline
- ✅ Auto-sync on app start
- ✅ Online event listeners
- ✅ Health check timeout (2s)
- ✅ FIFO sync order
- ✅ Retry limit (3)
- ✅ 409 conflict handling
- ✅ Manual retry UI
- ✅ Queue indicator visible
- ✅ Toast notifications
- ✅ Auto-navigate on sync
- ✅ Error handling
- ✅ AsyncStorage cleanup

---

**Status**: ✅ Ready for Production
