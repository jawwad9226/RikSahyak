import { useEffect, useState } from "react";
import { Alert, Linking, Pressable, StyleSheet, Text, View } from "react-native";

interface RideStatus {
  ride_id: string;
  status: string;
  passenger: string;
  pickup: string;
  dropoff: string;
  driver_name?: string;
  driver_phone?: string;
  vehicle_number?: string;
  current_location?: string;
  eta_minutes?: number;
}

export default function ActiveRide() {
  const [rideStatus, setRideStatus] = useState<RideStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching ride status
    const fetchRideStatus = async () => {
      try {
        // TODO: Replace with actual API call
        // const response = await fetch(`${API_BASE_URL}/api/v1/rides/status/${rideId}`);
        // const data = await response.json();

        // Dummy data for now
        const dummyStatus: RideStatus = {
          ride_id: "ride_001",
          status: "in_progress",
          passenger: "Raj",
          pickup: "Malkapur Station",
          dropoff: "Civil Lines",
          driver_name: "Ramesh Kumar",
          driver_phone: "+91-9876543210",
          vehicle_number: "MH-43-A-1234",
          current_location: "Near Bus Stand",
          eta_minutes: 5,
        };

        setRideStatus(dummyStatus);
      } catch (error) {
        Alert.alert("Error", "Failed to fetch ride status");
      } finally {
        setIsLoading(false);
      }
    };

    fetchRideStatus();

    // Poll for updates every 30 seconds
    const interval = setInterval(fetchRideStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleCallDriver = () => {
    if (rideStatus?.driver_phone) {
      Linking.openURL(`tel:${rideStatus.driver_phone}`);
    }
  };

  const handleCancelRide = () => {
    Alert.alert(
      "Cancel Ride",
      "Are you sure you want to cancel this ride?",
      [
        { text: "No", style: "cancel" },
        { text: "Yes", onPress: () => {
          // TODO: Call cancel API
          Alert.alert("Ride Cancelled", "Your ride has been cancelled.");
          setRideStatus(null);
        }},
      ]
    );
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Loading ride details...</Text>
      </View>
    );
  }

  if (!rideStatus) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>No Active Ride</Text>
        <Text style={styles.subtitle}>You don't have any active rides at the moment</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Your Ride</Text>

      <View style={styles.statusCard}>
        <Text style={styles.statusText}>
          Status: {rideStatus.status === "in_progress" ? "In Progress" : rideStatus.status}
        </Text>
      </View>

      <View style={styles.infoCard}>
        <View style={styles.routeContainer}>
          <Text style={styles.location}>{rideStatus.pickup}</Text>
          <Text style={styles.arrow}>↓</Text>
          <Text style={styles.location}>{rideStatus.dropoff}</Text>
        </View>

        {rideStatus.driver_name && (
          <View style={styles.driverInfo}>
            <Text style={styles.label}>Driver:</Text>
            <Text style={styles.value}>{rideStatus.driver_name}</Text>
          </View>
        )}

        {rideStatus.vehicle_number && (
          <View style={styles.driverInfo}>
            <Text style={styles.label}>Vehicle:</Text>
            <Text style={styles.value}>{rideStatus.vehicle_number}</Text>
          </View>
        )}

        {rideStatus.current_location && (
          <View style={styles.driverInfo}>
            <Text style={styles.label}>Current Location:</Text>
            <Text style={styles.value}>{rideStatus.current_location}</Text>
          </View>
        )}

        {rideStatus.eta_minutes && (
          <View style={styles.driverInfo}>
            <Text style={styles.label}>ETA:</Text>
            <Text style={styles.value}>{rideStatus.eta_minutes} minutes</Text>
          </View>
        )}
      </View>

      <View style={styles.buttonContainer}>
        <Pressable
          style={({ pressed }) => [
            styles.callButton,
            pressed && styles.pressed,
          ]}
          onPress={handleCallDriver}
        >
          <Text style={styles.callButtonText}>Call Driver</Text>
        </Pressable>

        <Pressable
          style={({ pressed }) => [
            styles.cancelButton,
            pressed && styles.pressed,
          ]}
          onPress={handleCancelRide}
        >
          <Text style={styles.cancelButtonText}>Cancel Ride</Text>
        </Pressable>
      </View>
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
  subtitle: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
  },
  statusCard: {
    backgroundColor: "#E8F5E8",
    borderWidth: 2,
    borderColor: "#4CAF50",
    borderRadius: 8,
    padding: 15,
    marginBottom: 20,
  },
  statusText: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#2E7D32",
    textAlign: "center",
  },
  infoCard: {
    backgroundColor: "#F9F9F9",
    borderWidth: 2,
    borderColor: "#FFC107",
    borderRadius: 8,
    padding: 15,
    marginBottom: 20,
  },
  routeContainer: {
    alignItems: "center",
    marginBottom: 15,
  },
  location: {
    fontSize: 16,
    fontWeight: "600",
    color: "#000",
  },
  arrow: {
    fontSize: 14,
    color: "#666",
    marginVertical: 5,
  },
  driverInfo: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  label: {
    fontSize: 14,
    color: "#666",
    fontWeight: "500",
  },
  value: {
    fontSize: 14,
    color: "#000",
    fontWeight: "600",
  },
  buttonContainer: {
    flexDirection: "row",
    justifyContent: "space-around",
  },
  callButton: {
    backgroundColor: "#4CAF50",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    flex: 1,
    marginRight: 10,
  },
  callButtonText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "bold",
    textAlign: "center",
  },
  cancelButton: {
    backgroundColor: "#F44336",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    flex: 1,
    marginLeft: 10,
  },
  cancelButtonText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "bold",
    textAlign: "center",
  },
  pressed: {
    opacity: 0.8,
  },
});
