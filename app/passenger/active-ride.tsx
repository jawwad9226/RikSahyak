import { API_CONFIG } from "@/src/config/env";
import { useUser } from "@/src/context/UserContext";
import { cancelRide, getRideStatus } from "@/src/services/api";
import { useEffect, useState } from "react";
import { Alert, Linking, Pressable, StyleSheet, Text, View } from "react-native";

interface RideStatus {
  ride_id: string;
  status: string;
  driver_progress?: string;
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
  const { user } = useUser();
  const [rideStatus, setRideStatus] = useState<RideStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [rideId, setRideId] = useState<string | null>(null);

  // Get active ride for this passenger
  useEffect(() => {
    const fetchActiveRide = async () => {
      try {
        if (!user?.user_id) {
          setIsLoading(false);
          return;
        }

        const response = await fetch(`${API_CONFIG.API_PREFIX}/rides/passenger/${user.user_id}`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        });

        if (response.ok) {
          const data = await response.json();
          if (data.ride_id) {
            setRideId(data.ride_id);
          }
        }
      } catch (error) {
        console.error("Error fetching active ride:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchActiveRide();
  }, [user?.user_id]);

  // Fetch ride status details when we have a ride ID
  useEffect(() => {
    if (!rideId) {
      setRideStatus(null);
      return;
    }

    const fetchRideStatus = async () => {
      try {
        const res = await getRideStatus(rideId);
        if (res.success && res.data) {
          const data: any = res.data;
          setRideStatus({
            ride_id: data.id || data.ride_id,
            status: data.status,
            driver_progress: data.driver_progress,
            passenger: data.passenger_name || "You",
            pickup: data.pickup_location,
            dropoff: data.dropoff_location,
            driver_name: data.driver_name,
            driver_phone: data.driver_phone,
            vehicle_number: data.vehicle_number,
            current_location: data.current_location,
            eta_minutes: data.eta_minutes,
          });
        }
      } catch (error) {
        console.error("Error fetching ride status:", error);
      }
    };

    fetchRideStatus();

    // Poll for updates every 3 seconds
    const interval = setInterval(fetchRideStatus, 3000);
    return () => clearInterval(interval);
  }, [rideId]);

  const handleCallDriver = () => {
    if (rideStatus?.driver_phone) {
      Linking.openURL(`tel:${rideStatus.driver_phone}`);
    } else {
      Alert.alert("Error", "Driver phone number not available");
    }
  };

  const renderTimeline = () => {
    const steps = [
      { id: "assigned", icon: "🚕", label: "Driver Assigned", active: true },
      { id: "on_way", icon: "🛣", label: "On the Way", active: rideStatus?.driver_progress === "ON_THE_WAY_TO_PICKUP" || rideStatus?.driver_progress === "ARRIVED_AT_PICKUP" || rideStatus?.driver_progress === "ON_THE_WAY_TO_DROPOFF" || rideStatus?.status === "in_progress" },
      { id: "arrived", icon: "📍", label: "Arrived", active: rideStatus?.driver_progress === "ARRIVED_AT_PICKUP" || rideStatus?.driver_progress === "ON_THE_WAY_TO_DROPOFF" },
      { id: "completed", icon: "✅", label: "Completed", active: rideStatus?.status === "completed" },
    ];

    return (
      <View style={styles.timelineContainer}>
        {steps.map((step, index) => (
          <View key={step.id}>
            <View style={styles.timelineStep}>
              <View style={[styles.stepCircle, step.active && styles.stepCircleActive]}>
                <Text style={[styles.stepIcon, step.active && styles.stepIconActive]}>{step.icon}</Text>
              </View>
              <Text style={[styles.stepLabel, step.active && styles.stepLabelActive]}>{step.label}</Text>
            </View>
            {index < steps.length - 1 && (
              <View style={[styles.stepConnector, steps[index + 1].active && styles.stepConnectorActive]} />
            )}
          </View>
        ))}
      </View>
    );
  };

  const handleCancelRide = () => {
    if (!rideId) return;
    
    Alert.alert(
      "Cancel Ride",
      "Are you sure you want to cancel this ride?",
      [
        { text: "No", style: "cancel" },
        { text: "Yes", onPress: async () => {
          try {
            const response = await cancelRide(rideId);
            if (response.success) {
              Alert.alert("Cancelled", "Your ride has been cancelled.");
              setRideId(null);
              setRideStatus(null);
            } else {
              Alert.alert("Error", response.error || "Failed to cancel ride");
            }
          } catch (error) {
            Alert.alert("Error", "Failed to cancel ride: " + String(error));
          }
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

      {renderTimeline()}

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
  timelineContainer: {
    marginBottom: 20,
    paddingHorizontal: 20,
  },
  timelineStep: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
  },
  stepCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: "#E0E0E0",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 15,
  },
  stepCircleActive: {
    backgroundColor: "#4CAF50",
  },
  stepIcon: {
    fontSize: 24,
    opacity: 0.5,
  },
  stepIconActive: {
    opacity: 1,
  },
  stepLabel: {
    fontSize: 14,
    color: "#999",
    fontWeight: "500",
  },
  stepLabelActive: {
    color: "#2E7D32",
    fontWeight: "bold",
  },
  stepConnector: {
    width: 2,
    height: 20,
    backgroundColor: "#E0E0E0",
    marginLeft: 24,
    marginBottom: 5,
  },
  stepConnectorActive: {
    backgroundColor: "#4CAF50",
  },
});
