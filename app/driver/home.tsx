import { useUser } from "@/src/context/UserContext";
import {
    acceptRide,
    completeRide,
    getDriverCurrentRide,
    getRequestedRides,
    startRide,
} from "@/src/services/api";
import { colors } from "@/src/utils/colors";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import {
    ActivityIndicator,
    FlatList,
    Pressable,
    RefreshControl,
    ScrollView,
    StyleSheet,
    Text,
    View,
} from "react-native";

interface Ride {
  id: string;
  pickup_location: string;
  dropoff_location: string;
  estimated_fare: number;
  distance_km: number;
  passenger_id: string;
  status: string;
}

export default function DriverHome() {
  const { user } = useUser();
  const router = useRouter();
  const [requestedRides, setRequestedRides] = useState<Ride[]>([]);
  const [currentRide, setCurrentRide] = useState<Ride | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    if (!user?.user_id) return;
    try {
      setLoading(true);
      // Load current assigned ride
      const currentRes = await getDriverCurrentRide(user.user_id);
      if (currentRes.success && currentRes.data) {
        const data: any = currentRes.data;
        // Data now returns ride object directly, not wrapped in a "ride" property
        setCurrentRide((data.ride_id || data.id) ? data : null);
      }

      // Load requested rides
      const requestedRes = await getRequestedRides();
      if (requestedRes.success && requestedRes.data) {
        const data: any = requestedRes.data;
        setRequestedRides(data.rides || []);
      }
    } catch (e) {
      console.error("Failed to load data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Poll every 15 seconds (reduced frequency to prevent excessive API calls)
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, [user?.user_id]);

  // Navigate to current-ride screen when ride is assigned
  useEffect(() => {
    if (currentRide && (currentRide.status === "DRIVER_ASSIGNED" || currentRide.status === "IN_PROGRESS")) {
      router.push("/driver/current-ride");
    }
  }, [currentRide, router]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleAccept = async (rideId: string) => {
    if (!user?.user_id) return;
    try {
      setLoading(true);
      const res = await acceptRide(rideId, user.user_id);
      if (res.success) {
        await loadData();
      } else {
        alert("Failed to accept ride");
      }
    } catch (e: any) {
      alert("Error: " + (e?.message ?? String(e)));
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    if (!currentRide) return;
    try {
      setLoading(true);
      const res = await startRide(currentRide.id);
      if (res.success) {
        await loadData();
      } else {
        alert("Failed to start ride");
      }
    } catch (e: any) {
      alert("Error: " + (e?.message ?? String(e)));
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    if (!currentRide) return;
    try {
      setLoading(true);
      const res = await completeRide(currentRide.id);
      if (res.success) {
        setCurrentRide(null);
        await loadData();
      } else {
        alert("Failed to complete ride");
      }
    } catch (e: any) {
      alert("Error: " + (e?.message ?? String(e)));
    } finally {
      setLoading(false);
    }
  };

  const renderRideCard = ({ item }: { item: Ride }) => (
    <View style={styles.rideCard}>
      <View style={styles.rideInfo}>
        <Text style={styles.location}>{item.pickup_location}</Text>
        <Text style={styles.arrow}>↓</Text>
        <Text style={styles.location}>{item.dropoff_location}</Text>
        <View style={styles.detailsRow}>
          <Text style={styles.detail}>{item.distance_km.toFixed(1)} km</Text>
          <Text style={styles.fareAmount}>₹{item.estimated_fare}</Text>
        </View>
      </View>
      <Pressable
        style={({ pressed }) => [styles.acceptButton, pressed && styles.pressed]}
        onPress={() => handleAccept(item.id)}
        disabled={loading}
      >
        <Text style={styles.acceptText}>Accept</Text>
      </Pressable>
    </View>
  );

  if (loading && !refreshing && requestedRides.length === 0 && !currentRide) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
    >
      {currentRide ? (
        <View style={styles.currentRideSection}>
          <Text style={styles.sectionTitle}>Current Ride</Text>
          <View style={styles.currentRideCard}>
            <View style={styles.statusBadge}>
              <Text style={styles.statusText}>{currentRide.status}</Text>
            </View>
            <Text style={styles.currentLocation}>{currentRide.pickup_location}</Text>
            <Text style={styles.arrow}>↓</Text>
            <Text style={styles.currentLocation}>{currentRide.dropoff_location}</Text>
            <View style={styles.currentDetailsRow}>
              <Text style={styles.currentDetail}>{currentRide.distance_km.toFixed(1)} km</Text>
              <Text style={styles.currentFare}>₹{currentRide.estimated_fare}</Text>
            </View>
            <View style={styles.actionButtons}>
              {currentRide.status === "DRIVER_ASSIGNED" && (
                <Pressable
                  style={({ pressed }) => [styles.startButton, pressed && styles.pressed]}
                  onPress={handleStart}
                  disabled={loading}
                >
                  <Text style={styles.startButtonText}>Start Ride</Text>
                </Pressable>
              )}
              {currentRide.status === "IN_PROGRESS" && (
                <Pressable
                  style={({ pressed }) => [styles.completeButton, pressed && styles.pressed]}
                  onPress={handleComplete}
                  disabled={loading}
                >
                  <Text style={styles.completeButtonText}>Complete Ride</Text>
                </Pressable>
              )}
            </View>
          </View>
        </View>
      ) : (
        <View style={styles.requestedSection}>
          <Text style={styles.title}>Available Ride Requests</Text>
          {requestedRides.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>No ride requests available</Text>
              <Text style={styles.emptyHint}>Pull down to refresh</Text>
            </View>
          ) : (
            <FlatList
              data={requestedRides}
              renderItem={renderRideCard}
              keyExtractor={(item) => item.id}
              scrollEnabled={false}
            />
          )}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FFF",
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  currentRideSection: {
    padding: 20,
  },
  requestedSection: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 15,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 20,
  },
  currentRideCard: {
    backgroundColor: colors.primary,
    borderWidth: 2,
    borderColor: "#000",
    borderRadius: 12,
    padding: 20,
  },
  statusBadge: {
    alignSelf: "flex-start",
    backgroundColor: "#000",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginBottom: 12,
  },
  statusText: {
    color: colors.primary,
    fontSize: 12,
    fontWeight: "bold",
  },
  currentLocation: {
    fontSize: 18,
    fontWeight: "700",
    color: "#000",
    marginVertical: 4,
  },
  currentDetailsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "rgba(0,0,0,0.2)",
  },
  currentDetail: {
    fontSize: 14,
    color: "#000",
    fontWeight: "600",
  },
  currentFare: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#000",
  },
  actionButtons: {
    marginTop: 16,
  },
  startButton: {
    backgroundColor: "#4CAF50",
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
    borderWidth: 2,
    borderColor: "#000",
  },
  startButtonText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "bold",
  },
  completeButton: {
    backgroundColor: "#000",
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
    borderWidth: 2,
    borderColor: colors.primary,
  },
  completeButtonText: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: "bold",
  },
  rideCard: {
    backgroundColor: "#F9F9F9",
    borderWidth: 2,
    borderColor: colors.primary,
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  rideInfo: {
    flex: 1,
  },
  location: {
    fontSize: 16,
    fontWeight: "600",
    color: "#000",
    marginVertical: 2,
  },
  arrow: {
    fontSize: 20,
    color: "#666",
    marginVertical: 4,
  },
  detailsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 8,
  },
  detail: {
    fontSize: 14,
    color: "#666",
  },
  fareAmount: {
    fontSize: 18,
    fontWeight: "bold",
    color: colors.primary,
  },
  acceptButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: "#000",
  },
  acceptText: {
    color: "#000",
    fontSize: 16,
    fontWeight: "bold",
  },
  pressed: {
    opacity: 0.7,
  },
  emptyState: {
    alignItems: "center",
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    color: "#666",
    marginBottom: 8,
  },
  emptyHint: {
    fontSize: 14,
    color: "#999",
  },
});
