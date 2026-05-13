import { apiGet } from "@/src/services/api";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

interface DashboardStats {
  totalRides: number;
  totalRevenue: number;
  activeDrivers: number;
  activeRides: number;
  todayRides: number;
  todayRevenue: number;
  totalPassengers: number;
  averageRating: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await apiGet<DashboardStats>("/admin/stats");
        if (response.success && response.data) {
          setStats(response.data);
        } else {
          setError(response.error || "Failed to fetch stats");
        }
      } catch (error) {
        console.error("Failed to fetch dashboard stats:", error);
        setError("Network error occurred");
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();

    // Refresh stats every 60 seconds
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#FFC107" />
        <Text style={styles.title}>Loading dashboard...</Text>
      </View>
    );
  }

  if (error || !stats) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Admin Dashboard</Text>
        <Text style={styles.errorText}>{error || "Unable to load dashboard data"}</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Admin Dashboard</Text>

      <Text style={styles.sectionTitle}>Today's Overview</Text>
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Today's Rides</Text>
          <Text style={styles.statValue}>{stats.todayRides}</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Today's Revenue</Text>
          <Text style={styles.statValue}>₹{stats.todayRevenue}</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Overall Statistics</Text>
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Total Rides</Text>
          <Text style={styles.statValue}>{stats.totalRides}</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Total Revenue</Text>
          <Text style={styles.statValue}>₹{stats.totalRevenue}</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Active Drivers</Text>
          <Text style={styles.statValue}>{stats.activeDrivers}</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Active Rides</Text>
          <Text style={styles.statValue}>{stats.activeRides}</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Total Passengers</Text>
          <Text style={styles.statValue}>{stats.totalPassengers}</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>Average Rating</Text>
          <Text style={styles.statValue}>{stats.averageRating}⭐</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <View style={styles.actionGrid}>
        <Pressable style={styles.actionCard} onPress={() => router.push("/admin/users")}>
          <Text style={styles.actionTitle}>User Management</Text>
          <Text style={styles.actionDesc}>Manage drivers and passengers</Text>
        </Pressable>
        <Pressable style={styles.actionCard} onPress={() => router.push("/admin/rides")}>
          <Text style={styles.actionTitle}>Ride Management</Text>
          <Text style={styles.actionDesc}>Monitor and control active rides</Text>
        </Pressable>
        <Pressable style={styles.actionCard} onPress={() => router.push("/admin/analytics")}>
          <Text style={styles.actionTitle}>Analytics</Text>
          <Text style={styles.actionDesc}>View detailed statistics and reports</Text>
        </Pressable>
        <Pressable style={styles.actionCard} onPress={() => router.push("/admin/settings")}>
          <Text style={styles.actionTitle}>System Settings</Text>
          <Text style={styles.actionDesc}>Configure app settings and pricing</Text>
        </Pressable>
        <Pressable style={styles.actionCard} onPress={() => router.push("/admin/system" as any)}>
          <Text style={styles.actionTitle}>Machine Health</Text>
          <Text style={styles.actionDesc}>Monitor server battery, temp & logs</Text>
        </Pressable>
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
  subtitle: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
  },
  errorText: {
    fontSize: 16,
    color: "#F44336",
    textAlign: "center",
    marginTop: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#000",
    marginTop: 20,
    marginBottom: 15,
  },
  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  statCard: {
    backgroundColor: "#F5F5F5",
    borderLeftWidth: 4,
    borderLeftColor: "#FFC107",
    padding: 15,
    borderRadius: 8,
    marginBottom: 15,
    width: "48%",
  },
  statLabel: {
    fontSize: 14,
    color: "#666",
  },
  statValue: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#000",
    marginTop: 5,
  },
  actionGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  actionCard: {
    backgroundColor: "#F9F9F9",
    borderWidth: 2,
    borderColor: "#E0E0E0",
    padding: 15,
    borderRadius: 8,
    marginBottom: 15,
    width: "48%",
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 5,
  },
  actionDesc: {
    fontSize: 12,
    color: "#666",
    lineHeight: 16,
  },
});
