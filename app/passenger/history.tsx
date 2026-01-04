import { useEffect, useState } from "react";
import { FlatList, StyleSheet, Text, View } from "react-native";

interface RideHistory {
  id: string;
  date: string;
  pickup: string;
  dropoff: string;
  fare: number;
  distance: number;
  status: string;
  driver_name?: string;
}

export default function History() {
  const [rideHistory, setRideHistory] = useState<RideHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching ride history
    const fetchRideHistory = async () => {
      try {
        // TODO: Replace with actual API call
        // const response = await fetch(`${API_BASE_URL}/api/v1/rides/history`);
        // const data = await response.json();

        // Dummy data for now
        const dummyHistory: RideHistory[] = [
          {
            id: "ride_001",
            date: "2024-01-15 14:30",
            pickup: "Malkapur Station",
            dropoff: "Civil Lines",
            fare: 65,
            distance: 3.2,
            status: "completed",
            driver_name: "Ramesh Kumar",
          },
          {
            id: "ride_002",
            date: "2024-01-14 09:15",
            pickup: "Bus Stand",
            dropoff: "Hospital",
            fare: 45,
            distance: 2.1,
            status: "completed",
            driver_name: "Suresh Patel",
          },
          {
            id: "ride_003",
            date: "2024-01-13 18:45",
            pickup: "Market",
            dropoff: "Station",
            fare: 55,
            distance: 2.8,
            status: "completed",
            driver_name: "Amit Singh",
          },
        ];

        setRideHistory(dummyHistory);
      } catch (error) {
        console.error("Failed to fetch ride history:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRideHistory();
  }, []);

  const renderRideItem = ({ item }: { item: RideHistory }) => (
    <View style={styles.rideCard}>
      <View style={styles.headerRow}>
        <Text style={styles.date}>{item.date}</Text>
        <Text style={[styles.status, getStatusStyle(item.status)]}>
          {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
        </Text>
      </View>

      <View style={styles.routeContainer}>
        <Text style={styles.location}>{item.pickup}</Text>
        <Text style={styles.arrow}>→</Text>
        <Text style={styles.location}>{item.dropoff}</Text>
      </View>

      <View style={styles.detailsRow}>
        <Text style={styles.detail}>{item.distance} km</Text>
        <Text style={styles.fareAmount}>₹{item.fare}</Text>
      </View>

      {item.driver_name && (
        <Text style={styles.driverName}>Driver: {item.driver_name}</Text>
      )}
    </View>
  );

  const getStatusStyle = (status: string) => {
    switch (status) {
      case "completed":
        return styles.statusCompleted;
      case "cancelled":
        return styles.statusCancelled;
      default:
        return styles.statusDefault;
    }
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Loading ride history...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Ride History</Text>

      {rideHistory.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>No rides completed yet</Text>
          <Text style={styles.emptySubtext}>Your completed rides will appear here</Text>
        </View>
      ) : (
        <FlatList
          data={rideHistory}
          renderItem={renderRideItem}
          keyExtractor={(item) => item.id}
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
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
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  emptyText: {
    fontSize: 18,
    fontWeight: "600",
    color: "#666",
    marginBottom: 10,
  },
  emptySubtext: {
    fontSize: 14,
    color: "#999",
    textAlign: "center",
  },
  rideCard: {
    backgroundColor: "#F9F9F9",
    borderWidth: 2,
    borderColor: "#FFC107",
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  date: {
    fontSize: 14,
    color: "#666",
  },
  status: {
    fontSize: 12,
    fontWeight: "bold",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    textAlign: "center",
  },
  statusCompleted: {
    backgroundColor: "#E8F5E8",
    color: "#2E7D32",
  },
  statusCancelled: {
    backgroundColor: "#FFEBEE",
    color: "#C62828",
  },
  statusDefault: {
    backgroundColor: "#FFF3E0",
    color: "#EF6C00",
  },
  routeContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
  },
  location: {
    fontSize: 16,
    fontWeight: "600",
    color: "#000",
    flex: 1,
  },
  arrow: {
    fontSize: 14,
    color: "#666",
    marginHorizontal: 10,
  },
  detailsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  detail: {
    fontSize: 14,
    color: "#666",
  },
  fareAmount: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#FFC107",
  },
  driverName: {
    fontSize: 14,
    color: "#666",
    fontStyle: "italic",
  },
});
