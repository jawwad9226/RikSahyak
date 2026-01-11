import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useState } from "react";

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
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Load user from storage on mount
  useEffect(() => {
    (async () => {
      try {
        const stored = await AsyncStorage.getItem("@user");
        if (stored) {
          setUserState(JSON.parse(stored));
        }
      } catch (e) {
        console.error("Failed to load user from storage:", e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const setUser = async (newUser: User) => {
    setUserState(newUser);
    await AsyncStorage.setItem("@user", JSON.stringify(newUser));
  };

  const logout = async () => {
    setUserState(null);
    await AsyncStorage.removeItem("@user");
  };

  return (
    <UserContext.Provider value={{ user, loading, setUser, logout }}>
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
