import { colors } from "@/src/utils/colors";
import React, { useState } from "react";
import { ActivityIndicator, Modal, Pressable, StyleSheet, Text, View } from "react-native";

const DEMO_USERS = {
  passenger: [
    { user_id: "PAS-001", name: "Raj Kumar", role: "passenger" as const },
    { user_id: "PAS-002", name: "Priya Singh", role: "passenger" as const },
  ],
  driver: [
    { user_id: "DRV-1001", name: "Ramesh", role: "driver" as const },
    { user_id: "DRV-1002", name: "Suresh", role: "driver" as const },
    { user_id: "DRV-1003", name: "Mahesh", role: "driver" as const },
  ],
  admin: [
    { user_id: "ADM-001", name: "Admin User", role: "admin" as const },
  ],
};

interface RoleSelectionModalProps {
  visible: boolean;
  onSelect: (user: { user_id: string; name?: string; role: "passenger" | "driver" | "admin" }) => void;
}

export function RoleSelectionModal({ visible, onSelect }: RoleSelectionModalProps) {
  const [role, setRole] = useState<"passenger" | "driver" | "admin" | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSelectRole = (selectedRole: "passenger" | "driver" | "admin") => {
    setRole(selectedRole);
    setUserId(null);
  };

  const handleSelectUser = async (user: { user_id: string; name?: string; role: "passenger" | "driver" | "admin" }) => {
    setLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 300));
      onSelect(user);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setRole(null);
    setUserId(null);
  };

  return (
    <Modal visible={visible} animationType="fade" transparent>
      <View style={styles.overlay}>
        <View style={styles.card}>
          {!role ? (
            // Role selection
            <>
              <Text style={styles.title}>Select Your Role</Text>
              <Pressable
                style={({ pressed }) => [styles.roleButton, pressed && styles.pressed]}
                onPress={() => handleSelectRole("passenger")}
              >
                <Text style={styles.roleButtonText}>🚶 Passenger</Text>
              </Pressable>
              <Pressable
                style={({ pressed }) => [styles.roleButton, styles.driverButton, pressed && styles.pressed]}
                onPress={() => handleSelectRole("driver")}
              >
                <Text style={styles.roleButtonText}>🚗 Driver</Text>
              </Pressable>
              <Pressable
                style={({ pressed }) => [styles.roleButton, styles.adminButton, pressed && styles.pressed]}
                onPress={() => handleSelectRole("admin")}
              >
                <Text style={styles.roleButtonText}>⚙️ Admin</Text>
              </Pressable>
            </>
          ) : (
            // User selection
            <>
              <Text style={styles.title}>Select {role === "passenger" ? "Passenger" : role === "driver" ? "Driver" : "Admin"}</Text>
              <View style={styles.userList}>
                {DEMO_USERS[role].map((user) => (
                  <Pressable
                    key={user.user_id}
                    style={({ pressed }) => [styles.userButton, pressed && styles.pressed]}
                    onPress={() => handleSelectUser(user)}
                    disabled={loading}
                  >
                    <Text style={styles.userButtonText}>{user.name}</Text>
                    <Text style={styles.userButtonSub}>{user.user_id}</Text>
                  </Pressable>
                ))}
              </View>
              <Pressable
                style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}
                onPress={handleBack}
                disabled={loading}
              >
                <Text style={styles.backButtonText}>← Back</Text>
              </Pressable>
            </>
          )}
          {loading && (
            <View style={styles.loadingOverlay}>
              <ActivityIndicator size="large" color={colors.primary} />
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.6)",
    justifyContent: "center",
    alignItems: "center",
  },
  card: {
    width: "85%",
    backgroundColor: "#FFF",
    borderRadius: 12,
    padding: 24,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  title: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 20,
    textAlign: "center",
  },
  roleButton: {
    backgroundColor: colors.primary,
    paddingVertical: 16,
    borderRadius: 8,
    marginBottom: 12,
    alignItems: "center",
    borderWidth: 2,
    borderColor: "#000",
  },
  driverButton: {
    backgroundColor: "#FFC107",
  },
  adminButton: {
    backgroundColor: "#333",
  },
  roleButtonText: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#000",
  },
  userList: {
    gap: 10,
    marginBottom: 16,
  },
  userButton: {
    backgroundColor: "#F5F5F5",
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#ddd",
  },
  userButtonText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#000",
  },
  userButtonSub: {
    fontSize: 12,
    color: "#666",
    marginTop: 4,
  },
  backButton: {
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
    backgroundColor: "#E0E0E0",
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#000",
  },
  pressed: {
    opacity: 0.7,
  },
  loadingOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(255, 255, 255, 0.7)",
    justifyContent: "center",
    alignItems: "center",
    borderRadius: 12,
  },
});
