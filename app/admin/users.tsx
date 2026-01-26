import { apiGet, apiPost } from "@/src/services/api";
import { useEffect, useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

interface User {
  id: string;
  role: string;
  name?: string;
  phone?: string;
  vehicle_number?: string;
  total_rides?: number;
  last_ride?: string;
  blocked?: boolean;
}

interface UsersData {
  drivers: User[];
  passengers: User[];
  total_drivers: number;
  total_passengers: number;
}

export default function UserManagement() {
  const [users, setUsers] = useState<UsersData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"drivers" | "passengers">("drivers");

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const response = await apiGet<UsersData>("/admin/users");
      if (response.success && response.data) {
        setUsers(response.data);
      }
    } catch (error) {
      console.error("Failed to fetch users:", error);
      Alert.alert("Error", "Failed to load users");
    } finally {
      setIsLoading(false);
    }
  };

  const handleBlockUser = async (userId: string, userType: string) => {
    // Find the user to check if they're blocked
    const allUsers = [...(users?.drivers || []), ...(users?.passengers || [])];
    const user = allUsers.find(u => u.id === userId);
    const isBlocked = user?.blocked || false;

    const action = isBlocked ? "unblock" : "block";
    const endpoint = `/admin/users/${userId}/${action}`;

    Alert.alert(
      `${action.charAt(0).toUpperCase() + action.slice(1)} User`,
      `Are you sure you want to ${action} this ${userType}?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: action,
          style: isBlocked ? "default" : "destructive",
          onPress: async () => {
            try {
              const response = await apiPost(endpoint, {});
              if (response.success) {
                Alert.alert("Success", `${userType} ${action}ed successfully`);
                fetchUsers(); // Refresh the list
              } else {
                Alert.alert("Error", response.error || `Failed to ${action} user`);
              }
            } catch (error) {
              Alert.alert("Error", `Failed to ${action} user`);
            }
          }
        }
      ]
    );
  };

  const filteredUsers = users ? (
    activeTab === "drivers"
      ? users.drivers.filter(user =>
          user.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          user.phone?.includes(searchQuery) ||
          user.id.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : users.passengers.filter(user =>
          user.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          user.phone?.includes(searchQuery) ||
          user.id.toLowerCase().includes(searchQuery.toLowerCase())
        )
  ) : [];

  const renderUserCard = (user: User) => (
    <View key={user.id} style={styles.userCard}>
      <View style={styles.userInfo}>
        <Text style={styles.userName}>{user.name || "Unknown"}</Text>
        <Text style={styles.userId}>ID: {user.id}</Text>
        <Text style={styles.userPhone}>{user.phone || "No phone"}</Text>
        {user.role === "driver" && (
          <Text style={styles.userVehicle}>
            Vehicle: {user.vehicle_number || "Not set"}
          </Text>
        )}
        {user.role === "passenger" && (
          <Text style={styles.userStats}>
            Total Rides: {user.total_rides || 0}
          </Text>
        )}
        {user.blocked && (
          <Text style={styles.blockedBadge}>BLOCKED</Text>
        )}
      </View>
      <View style={styles.userActions}>
        <Pressable
          style={[styles.actionButton, styles.blockButton]}
          onPress={() => handleBlockUser(user.id, user.role)}
        >
          <Text style={styles.blockButtonText}>
            {user.blocked ? "Unblock" : "Block"}
          </Text>
        </Pressable>
      </View>
    </View>
  );

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>User Management</Text>
        <Text style={styles.loadingText}>Loading users...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>User Management</Text>

      <View style={styles.summaryCards}>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryValue}>{users?.total_drivers || 0}</Text>
          <Text style={styles.summaryLabel}>Total Drivers</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryValue}>{users?.total_passengers || 0}</Text>
          <Text style={styles.summaryLabel}>Total Passengers</Text>
        </View>
      </View>

      <TextInput
        style={styles.searchInput}
        placeholder="Search by name, phone, or ID..."
        value={searchQuery}
        onChangeText={setSearchQuery}
      />

      <View style={styles.tabContainer}>
        <Pressable
          style={[styles.tab, activeTab === "drivers" && styles.activeTab]}
          onPress={() => setActiveTab("drivers")}
        >
          <Text style={[styles.tabText, activeTab === "drivers" && styles.activeTabText]}>
            Drivers ({users?.drivers.length || 0})
          </Text>
        </Pressable>
        <Pressable
          style={[styles.tab, activeTab === "passengers" && styles.activeTab]}
          onPress={() => setActiveTab("passengers")}
        >
          <Text style={[styles.tabText, activeTab === "passengers" && styles.activeTabText]}>
            Passengers ({users?.passengers.length || 0})
          </Text>
        </Pressable>
      </View>

      <View style={styles.usersList}>
        {filteredUsers.map(renderUserCard)}
        {filteredUsers.length === 0 && (
          <Text style={styles.noUsersText}>No users found</Text>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: "#FFF",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 20,
  },
  loadingText: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
  },
  summaryCards: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 20,
  },
  summaryCard: {
    backgroundColor: "#F5F5F5",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
    width: "48%",
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#000",
  },
  summaryLabel: {
    fontSize: 14,
    color: "#666",
    marginTop: 5,
  },
  searchInput: {
    borderWidth: 1,
    borderColor: "#DDD",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 15,
  },
  tabContainer: {
    flexDirection: "row",
    marginBottom: 15,
  },
  tab: {
    flex: 1,
    padding: 12,
    alignItems: "center",
    backgroundColor: "#F5F5F5",
    marginHorizontal: 5,
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: "#FFC107",
  },
  tabText: {
    fontSize: 16,
    fontWeight: "500",
    color: "#666",
  },
  activeTabText: {
    color: "#000",
  },
  usersList: {
    marginBottom: 20,
  },
  userCard: {
    backgroundColor: "#F9F9F9",
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 4,
  },
  userId: {
    fontSize: 12,
    color: "#666",
    marginBottom: 2,
  },
  userPhone: {
    fontSize: 14,
    color: "#333",
    marginBottom: 2,
  },
  userVehicle: {
    fontSize: 14,
    color: "#333",
    marginBottom: 2,
  },
  userStats: {
    fontSize: 14,
    color: "#333",
  },
  blockedBadge: {
    fontSize: 12,
    color: "#FF4444",
    fontWeight: "bold",
    marginTop: 4,
  },
  userActions: {
    flexDirection: "row",
  },
  actionButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginLeft: 8,
  },
  blockButton: {
    backgroundColor: "#FF4444",
  },
  blockButtonText: {
    color: "#FFF",
    fontSize: 14,
    fontWeight: "500",
  },
  noUsersText: {
    textAlign: "center",
    fontSize: 16,
    color: "#666",
    marginTop: 20,
  },
});