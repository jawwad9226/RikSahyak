import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useState } from "react";
import { flushQueue, onQueuedRideSynced } from "@/src/services/api";
import { setupConnectivityListener } from "@/src/utils/connectivityHelpers";

interface User {
  user_id: string;
  role: "passenger" | "driver" | "admin";
  name?: string;
}

interface UserContextType {
  user: User | null;
  loading: boolean;
  setUser: (user: User) => Promise<void>;
  logout: () => Promise<void>;
  queuedRideId?: string; // When a queued ride is synced
  setQueuedRideId: (id: string | undefined) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [queuedRideId, setQueuedRideId] = useState<string | undefined>();

  // Load user from storage and setup auto-sync on mount
  useEffect(() => {
    (async () => {
      try {
        // Load user
        const stored = await AsyncStorage.getItem("@user");
        if (stored) {
          setUserState(JSON.parse(stored));
        }

        // On app start, flush queue
        console.log("[SYNC] Starting app, flushing queue...");
        const synced = await flushQueue();
        console.log(`[SYNC] Flushed ${synced} queued requests`);

        // Register callback for when queued rides are synced
        onQueuedRideSynced((queuedItem, rideResponse) => {
          if (rideResponse?.ride_id) {
            setQueuedRideId(rideResponse.ride_id);
          }
        });
      } catch (e) {
        console.error("Failed to initialize app:", e);
      } finally {
        setLoading(false);
      }
    })();

    // Setup online/offline listeners
    const cleanup = setupConnectivityListener(
      () => {
        console.log("[CONNECTIVITY] Device came online");
        // Try to flush queue when device comes online
        flushQueue().then((synced) => {
          if (synced > 0) {
            console.log(`[SYNC] Flushed ${synced} queued requests on reconnect`);
          }
        });
      },
      () => {
        console.log("[CONNECTIVITY] Device went offline");
      }
    );

    return cleanup;
  }, []);

  const setUser = async (newUser: User) => {
    setUserState(newUser);
    await AsyncStorage.setItem("@user", JSON.stringify(newUser));
  };

  const logout = async () => {
    setUserState(null);
    setQueuedRideId(undefined);
    await AsyncStorage.removeItem("@user");
  };

  return (
    <UserContext.Provider value={{ user, loading, setUser, logout, queuedRideId, setQueuedRideId }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUser must be used within UserProvider");
  }
  return context;
}
