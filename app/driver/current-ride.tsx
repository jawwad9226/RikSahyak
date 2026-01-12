import { API_CONFIG } from "@/src/config/env";
import { useUser } from "@/src/context/UserContext";
import { completeRide, getRideStatus, startRide, updateDriverProgress } from "@/src/services/api";
import { useEffect, useState } from "react";
import { Alert, Linking, Pressable, StyleSheet, Text, View } from "react-native";

interface CurrentRide {
  ride_id: string;
  status: string;
  driver_progress?: string;
  passenger_name: string;
  passenger_phone: string;
  pickup: string;
  dropoff: string;
  fare: number;
  distance: number;
}

// Progress states
type ProgressState = "NOT_STARTED" | "ON_THE_WAY_TO_PICKUP" | "ARRIVED_AT_PICKUP" | "ON_THE_WAY_TO_DROPOFF";

export default function CurrentRide() {
  const { user } = useUser();
  const [currentRide, setCurrentRide] = useState<CurrentRide | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [rideId, setRideId] = useState<string | null>(null);
  const [isUpdatingProgress, setIsUpdatingProgress] = useState(false);

  // Get current ride for this driver
  useEffect(() => {
    const fetchCurrentRide = async () => {
      try {
        if (!user?.user_id) {
          setIsLoading(false);
          return;
        }

        const response = await fetch(`${API_CONFIG.API_PREFIX}/rides/driver/${user.user_id}/current`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        });

        if (response.ok) {
          const data = await response.json();
          if (data.ride_id || data.id) {
            setRideId(data.ride_id || data.id);
          }
        }
      } catch (error) {
        console.error("Error fetching current ride:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCurrentRide();
  }, [user?.user_id]);

  // Fetch ride details when we have a ride ID
  useEffect(() => {
    if (!rideId) {
      setCurrentRide(null);
      return;
    }

    const fetchRideDetails = async () => {
      try {
        const res = await getRideStatus(rideId);
        if (res.success && res.data) {
          const data: any = res.data;
          setCurrentRide({
            ride_id: data.id || data.ride_id,
            status: data.status,
            driver_progress: data.driver_progress,
            passenger_name: data.passenger_name || "Passenger",
            passenger_phone: data.passenger_phone || "",
            pickup: data.pickup_location,
            dropoff: data.dropoff_location,
            fare: data.estimated_fare || data.fare || 0,
            distance: data.distance_km || 0,
          });
        }
      } catch (error) {
        console.error("Error fetching ride details:", error);
      }
    };

    fetchRideDetails();

    // Poll for updates every 3 seconds
    const interval = setInterval(fetchRideDetails, 3000);
    return () => clearInterval(interval);
  }, [rideId]);

  const handleCallPassenger = () => {
    if (currentRide?.passenger_phone) {
      Linking.openURL(`tel:${currentRide.passenger_phone}`);
    } else {
      Alert.alert("Error", "Passenger phone number not available");
    }
  };

  const handleCompleteRide = async () => {
    if (!rideId) return;

    Alert.alert(
      "Complete Ride",
      "Mark this ride as completed?",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Complete", onPress: async () => {
          try {
            const response = await completeRide(rideId, user?.user_id);
            if (response.success) {
              Alert.alert("Completed", "Ride marked as completed. Earnings updated.");
              setRideId(null);
              setCurrentRide(null);
            } else {
              Alert.alert("Error", response.error || "Failed to complete ride");
            }
          } catch (error) {
            Alert.alert("Error", "Failed to complete ride: " + String(error));
          }
        }},
      ]
    );
  };

  const handleStartRide = async () => {
    if (!rideId) return;

    Alert.alert(
      "Start Ride",
      "Confirm pickup and start the ride?",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Start", onPress: async () => {
          try {
            const response = await startRide(rideId, user?.user_id);
            if (response.success) {
              Alert.alert("Started", "Ride started. Safe journey!");
              if (currentRide) {
                setCurrentRide({ ...currentRide, status: "IN_PROGRESS" });
              }
            } else {
              Alert.alert("Error", response.error || "Failed to start ride");
            }
          } catch (error) {
            Alert.alert("Error", "Failed to start ride: " + String(error));
          }
        }},
      ]
    );
  };

  const handleUpdateProgress = async (nextProgress: ProgressState) => {
    if (!rideId || !user?.user_id) return;

    const progressLabels: Record<ProgressState, string> = {
      NOT_STARTED: "Reset progress",
      ON_THE_WAY_TO_PICKUP: "On the way to pickup",
      ARRIVED_AT_PICKUP: "Arrived at pickup",
      ON_THE_WAY_TO_DROPOFF: "On the way to dropoff",
    };

    Alert.alert(
      "Update Progress",
      `Mark as "${progressLabels[nextProgress]}"?`,
      [
        { text: "Cancel", style: "cancel" },
        { 
          text: "Update", 
          onPress: async () => {
            try {
              setIsUpdatingProgress(true);
              const response = await updateDriverProgress(rideId, user.user_id, nextProgress);
              if (response.success) {
                if (currentRide) {
                  setCurrentRide({ ...currentRide, driver_progress: nextProgress });
                }
                Alert.alert("Updated", `Progress updated to ${progressLabels[nextProgress]}`);
              } else {
                Alert.alert("Error", response.error || "Failed to update progress");
              }
            } catch (error) {
              Alert.alert("Error", "Failed to update progress: " + String(error));
            } finally {
              setIsUpdatingProgress(false);
            }
          }
        },
      ]
    );
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Loading current ride...</Text>
      </View>
    );
  }

  if (!currentRide) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>No Active Ride</Text>
        <Text style={styles.subtitle}>You don't have any active rides at the moment</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Current Ride</Text>

      <View style={styles.statusCard}>
        <Text style={styles.statusText}>
          Status: {currentRide.status === "accepted" ? "Waiting for Pickup" :
                   currentRide.status === "in_progress" ? "In Progress" :
                   currentRide.status}
        </Text>
      </View>

      {/* Driver Progress Display */}
      {currentRide.status !== "completed" && currentRide.status !== "cancelled" && (
        <View style={styles.progressCard}>
          <Text style={styles.progressLabel}>Progress:</Text>
          <Text style={styles.progressValue}>
            {currentRide.driver_progress === "NOT_STARTED" || !currentRide.driver_progress
              ? "Not Started"
              : currentRide.driver_progress === "ON_THE_WAY_TO_PICKUP"
              ? "On the way to pickup"
              : currentRide.driver_progress === "ARRIVED_AT_PICKUP"
              ? "Arrived at pickup"
              : currentRide.driver_progress === "ON_THE_WAY_TO_DROPOFF"
              ? "On the way to dropoff"
              : currentRide.driver_progress}
          </Text>
        </View>
      )}

      <View style={styles.infoCard}>
        <View style={styles.passengerInfo}>
          <Text style={styles.label}>Passenger:</Text>
          <Text style={styles.value}>{currentRide.passenger_name}</Text>
        </View>

        <View style={styles.routeContainer}>
          <Text style={styles.location}>{currentRide.pickup}</Text>
          <Text style={styles.arrow}>↓</Text>
          <Text style={styles.location}>{currentRide.dropoff}</Text>
        </View>

        <View style={styles.detailsRow}>
          <Text style={styles.detail}>{currentRide.distance} km</Text>
          <Text style={styles.fareAmount}>₹{currentRide.fare}</Text>
        </View>
      </View>

      <View style={styles.buttonContainer}>
        <Pressable
          style={({ pressed }) => [
            styles.callButton,
            pressed && styles.pressed,
          ]}
          onPress={handleCallPassenger}
        >
          <Text style={styles.callButtonText}>Call Passenger</Text>
        </Pressable>

        {/* Progress Update Buttons */}
        {currentRide.status !== "completed" && currentRide.status !== "cancelled" && (
          <View style={styles.progressButtonContainer}>
            {(!currentRide.driver_progress || currentRide.driver_progress === "NOT_STARTED") && (
              <Pressable
                style={({ pressed }) => [
                  styles.progressButton,
                  styles.progressButtonWay,
                  pressed && styles.pressed,
                  isUpdatingProgress && styles.disabled,
                ]}
                onPress={() => handleUpdateProgress("ON_THE_WAY_TO_PICKUP")}
                disabled={isUpdatingProgress}
              >
                <Text style={styles.progressButtonText}>On the way</Text>
              </Pressable>
            )}

            {currentRide.driver_progress === "ON_THE_WAY_TO_PICKUP" && (
              <Pressable
                style={({ pressed }) => [
                  styles.progressButton,
                  styles.progressButtonArrive,
                  pressed && styles.pressed,
                  isUpdatingProgress && styles.disabled,
                ]}
                onPress={() => handleUpdateProgress("ARRIVED_AT_PICKUP")}
                disabled={isUpdatingProgress}
              >
                <Text style={styles.progressButtonText}>Arrived at pickup</Text>
              </Pressable>
            )}

            {currentRide.driver_progress === "ARRIVED_AT_PICKUP" && (
              <Pressable
                style={({ pressed }) => [
                  styles.progressButton,
                  styles.progressButtonDrop,
                  pressed && styles.pressed,
                  isUpdatingProgress && styles.disabled,
                ]}
                onPress={() => handleUpdateProgress("ON_THE_WAY_TO_DROPOFF")}
                disabled={isUpdatingProgress}
              >
                <Text style={styles.progressButtonText}>Going to drop</Text>
              </Pressable>
            )}
          </View>
        )}

        {currentRide.status === "accepted" && (
          <Pressable
            style={({ pressed }) => [
              styles.startButton,
              pressed && styles.pressed,
            ]}
            onPress={handleStartRide}
          >
            <Text style={styles.startButtonText}>Start Ride</Text>
          </Pressable>
        )}

        {currentRide.status === "in_progress" && (
          <Pressable
            style={({ pressed }) => [
              styles.completeButton,
              pressed && styles.pressed,
            ]}
            onPress={handleCompleteRide}
          >
            <Text style={styles.completeButtonText}>Complete Ride</Text>
          </Pressable>
        )}
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
    backgroundColor: "#E3F2FD",
    borderWidth: 2,
    borderColor: "#2196F3",
    borderRadius: 8,
    padding: 15,
    marginBottom: 20,
  },
  statusText: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#0D47A1",
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
  passengerInfo: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 15,
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
  detailsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
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
  buttonContainer: {
    gap: 10,
  },
  callButton: {
    backgroundColor: "#4CAF50",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  callButtonText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "bold",
  },
  startButton: {
    backgroundColor: "#FF9800",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  startButtonText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "bold",
  },
  completeButton: {
    backgroundColor: "#2196F3",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  completeButtonText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "bold",
  },
  pressed: {
    opacity: 0.8,
  },
  progressCard: {
    backgroundColor: "#E8F5E9",
    borderWidth: 2,
    borderColor: "#4CAF50",
    borderRadius: 8,
    padding: 15,
    marginBottom: 20,
  },
  progressLabel: {
    fontSize: 12,
    color: "#666",
    textTransform: "uppercase",
    fontWeight: "600",
    marginBottom: 5,
  },
  progressValue: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#1B5E20",
  },
  progressButtonContainer: {
    gap: 10,
    marginBottom: 10,
  },
  progressButton: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
    borderWidth: 2,
  },
  progressButtonWay: {
    backgroundColor: "#FFE082",
    borderColor: "#F57F17",
  },
  progressButtonArrive: {
    backgroundColor: "#81C784",
    borderColor: "#2E7D32",
  },
  progressButtonDrop: {
    backgroundColor: "#64B5F6",
    borderColor: "#1565C0",
  },
  progressButtonText: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#FFF",
  },
  disabled: {
    opacity: 0.5,
  },
});
