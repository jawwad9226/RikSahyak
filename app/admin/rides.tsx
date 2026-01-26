import { apiGet, apiPost } from "@/src/services/api";
import { useEffect, useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

interface Ride {
  id: string;
  status: string;
  passenger_name?: string;
  passenger_phone?: string;
  driver_name?: string;
  driver_phone?: string;
  pickup_location: string;
  dropoff_location: string;
  estimated_fare: number;
  created_at?: string;
  passenger_feedback?: any;
}

interface RidesData {
  rides: Ride[];
  total: number;
  status_filter?: string;
}

export default function RideManagement() {
  const [rides, setRides] = useState<RidesData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchRides();
  }, [statusFilter]);

  const fetchRides = async () => {
    try {
      setIsLoading(true);
      const params = statusFilter ? `?status=${statusFilter}` : "";
      const response = await apiGet<RidesData>(`/admin/rides${params}`);
      if (response.success && response.data) {
        setRides(response.data);
      }
    } catch (error) {
      console.error("Failed to fetch rides:", error);
      Alert.alert("Error", "Failed to load rides");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReassignRide = async (rideId: string) => {
    Alert.alert(
      "Reassign Ride",
      "Find a new driver for this ride?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Reassign",
          onPress: async () => {
            try {
              const response = await apiPost(`/admin/rides/${rideId}/reassign`, {});
              if (response.success) {
                Alert.alert("Success", "Ride reassigned successfully");
                fetchRides(); // Refresh the list
              } else {
                Alert.alert("Error", response.error || "Failed to reassign ride");
              }
            } catch (error) {
              Alert.alert("Error", "Failed to reassign ride");
            }
          }
        }
      ]
    );
  };

  const handleCancelRide = async (rideId: string) => {
    Alert.alert(
      "Cancel Ride",
      "Are you sure you want to cancel this ride?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Confirm Cancel",
          style: "destructive",
          onPress: async () => {
            try {
              const response = await apiPost(`/admin/rides/${rideId}/cancel`, {});
              if (response.success) {
                Alert.alert("Success", "Ride cancelled successfully");
                fetchRides(); // Refresh the list
              } else {
                Alert.alert("Error", response.error || "Failed to cancel ride");
              }
            } catch (error) {
              Alert.alert("Error", "Failed to cancel ride");
            }
          }
        }
      ]
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "REQUESTED": return "#FFC107";
      case "DRIVER_ASSIGNED": return "#2196F3";
      case "IN_PROGRESS": return "#4CAF50";
      case "COMPLETED": return "#2E7D32";
      case "CANCELLED": return "#F44336";
      default: return "#666";
    }
  };

  const filteredRides = rides ? rides.rides.filter(ride =>
    ride.passenger_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ride.driver_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ride.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ride.pickup_location.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ride.dropoff_location.toLowerCase().includes(searchQuery.toLowerCase())
  ) : [];

  const renderRideCard = (ride: Ride) => (
    <View key={ride.id} style={styles.rideCard}>
      <View style={styles.rideHeader}>
        <Text style={styles.rideId}>Ride #{ride.id.slice(-4)}</Text>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(ride.status) }]}>
          <Text style={styles.statusText}>{ride.status}</Text>
        </View>
      </View>

      <View style={styles.rideDetails}>
        <View style={styles.detailRow}>
          <Text style={styles.label}>Passenger:</Text>
          <Text style={styles.value}>{ride.passenger_name || "Unknown"}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.label}>Phone:</Text>
          <Text style={styles.value}>{ride.passenger_phone || "N/A"}</Text>
        </View>
        {ride.driver_name && (
          <>
            <View style={styles.detailRow}>
              <Text style={styles.label}>Driver:</Text>
              <Text style={styles.value}>{ride.driver_name}</Text>
            </View>
            <View style={styles.detailRow}>
              <Text style={styles.label}>Driver Phone:</Text>
              <Text style={styles.value}>{ride.driver_phone || "N/A"}</Text>
            </View>
          </>
        )}
        <View style={styles.routeContainer}>
          <Text style={styles.location}>{ride.pickup_location}</Text>
          <Text style={styles.arrow}>→</Text>
          <Text style={styles.location}>{ride.dropoff_location}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.label}>Fare:</Text>
          <Text style={styles.fareValue}>₹{ride.estimated_fare}</Text>
        </View>
        {ride.created_at && (
          <View style={styles.detailRow}>
            <Text style={styles.label}>Created:</Text>
            <Text style={styles.value}>
              {new Date(ride.created_at).toLocaleString()}
            </Text>
          </View>
        )}
        {ride.passenger_feedback && (
          <View style={styles.feedbackContainer}>
            <Text style={styles.feedbackLabel}>Feedback: {ride.passenger_feedback.rating}⭐</Text>
            {ride.passenger_feedback.feedback_text && (
              <Text style={styles.feedbackText}>"{ride.passenger_feedback.feedback_text}"</Text>
            )}
          </View>
        )}
      </View>

      {(ride.status === "REQUESTED" || ride.status === "DRIVER_ASSIGNED") && (
        <View style={styles.rideActions}>
          {ride.status === "DRIVER_ASSIGNED" && (
            <Pressable
              style={[styles.actionButton, styles.reassignButton]}
              onPress={() => handleReassignRide(ride.id)}
            >
              <Text style={styles.reassignButtonText}>Reassign</Text>
            </Pressable>
          )}
          <Pressable
            style={[styles.actionButton, styles.cancelButton]}
            onPress={() => handleCancelRide(ride.id)}
          >
            <Text style={styles.cancelButtonText}>Cancel Ride</Text>
          </Pressable>
        </View>
      )}
    </View>
  );

  const statusOptions = ["", "REQUESTED", "DRIVER_ASSIGNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"];

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Ride Management</Text>
        <Text style={styles.loadingText}>Loading rides...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Ride Management</Text>

      <View style={styles.summaryCard}>
        <Text style={styles.summaryValue}>{rides?.total || 0}</Text>
        <Text style={styles.summaryLabel}>Total Rides</Text>
      </View>

      <TextInput
        style={styles.searchInput}
        placeholder="Search by passenger, driver, location, or ride ID..."
        value={searchQuery}
        onChangeText={setSearchQuery}
      />

      <View style={styles.filterContainer}>
        <Text style={styles.filterLabel}>Filter by Status:</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
          {statusOptions.map((status) => (
            <Pressable
              key={status}
              style={[styles.filterButton, statusFilter === status && styles.activeFilter]}
              onPress={() => setStatusFilter(status)}
            >
              <Text style={[styles.filterText, statusFilter === status && styles.activeFilterText]}>
                {status || "All"}
              </Text>
            </Pressable>
          ))}
        </ScrollView>
      </View>

      <View style={styles.ridesList}>
        {filteredRides.map(renderRideCard)}
        {filteredRides.length === 0 && (
          <Text style={styles.noRidesText}>No rides found</Text>
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
  summaryCard: {
    backgroundColor: "#F5F5F5",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
    marginBottom: 15,
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
  filterContainer: {
    marginBottom: 15,
  },
  filterLabel: {
    fontSize: 16,
    fontWeight: "500",
    color: "#000",
    marginBottom: 8,
  },
  filterScroll: {
    marginBottom: 5,
  },
  filterButton: {
    backgroundColor: "#F5F5F5",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
  },
  activeFilter: {
    backgroundColor: "#FFC107",
  },
  filterText: {
    fontSize: 14,
    color: "#666",
  },
  activeFilterText: {
    color: "#000",
    fontWeight: "500",
  },
  ridesList: {
    marginBottom: 20,
  },
  rideCard: {
    backgroundColor: "#F9F9F9",
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
  },
  rideHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  rideId: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#000",
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: "bold",
    color: "#FFF",
  },
  rideDetails: {
    marginBottom: 10,
  },
  detailRow: {
    flexDirection: "row",
    marginBottom: 4,
  },
  label: {
    fontSize: 14,
    fontWeight: "500",
    color: "#666",
    width: 80,
  },
  value: {
    fontSize: 14,
    color: "#000",
    flex: 1,
  },
  routeContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 8,
    paddingVertical: 8,
    backgroundColor: "#F0F0F0",
    borderRadius: 6,
    paddingHorizontal: 10,
  },
  location: {
    fontSize: 14,
    color: "#000",
    flex: 1,
  },
  arrow: {
    fontSize: 16,
    color: "#666",
    marginHorizontal: 8,
  },
  fareValue: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#2E7D32",
  },
  feedbackContainer: {
    backgroundColor: "#FFF3E0",
    padding: 8,
    borderRadius: 6,
    marginTop: 8,
  },
  feedbackLabel: {
    fontSize: 14,
    fontWeight: "500",
    color: "#E65100",
  },
  feedbackText: {
    fontSize: 13,
    color: "#333",
    fontStyle: "italic",
    marginTop: 4,
  },
  rideActions: {
    flexDirection: "row",
    justifyContent: "flex-end",
  },
  actionButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  cancelButton: {
    backgroundColor: "#F44336",
  },
  cancelButtonText: {
    color: "#FFF",
    fontSize: 14,
    fontWeight: "500",
  },
  reassignButton: {
    backgroundColor: "#FFC107",
    marginRight: 8,
  },
  reassignButtonText: {
    color: "#000",
    fontSize: 14,
    fontWeight: "500",
  },
  noRidesText: {
    textAlign: "center",
    fontSize: 16,
    color: "#666",
    marginTop: 20,
  },
});