import { API_CONFIG } from "@/src/config/env";
import { useUser } from "@/src/context/UserContext";
import { cancelRide, getRideStatus } from "@/src/services/api";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Alert, Linking, Platform, Pressable, StyleSheet, Text, View } from "react-native";
import RideFeedback from "./ride-feedback";

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
  pickup_otp?: string; // Added OTP
  passenger_feedback?: any; // Added feedback tracking
}

export default function ActiveRide() {
  const { user } = useUser();
  const router = useRouter();
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
            pickup_otp: data.pickup_otp, // Added
            passenger_feedback: data.passenger_feedback, // Added
          });
        }
      } catch (error) {
        console.error("Error fetching ride status:", error);
      }
    };

    fetchRideStatus();

    // Poll for updates every 10 seconds (reduced frequency to prevent excessive API calls)
    const interval = setInterval(fetchRideStatus, 10000);
    return () => clearInterval(interval);
  }, [rideId]);

  const handleCallDriver = () => {
    if (!rideStatus?.driver_phone) {
      Alert.alert("Error", "Driver phone number not available");
      return;
    }

    if (Platform.OS === "web") {
      // On web, show an alert with the phone number and copy option
      Alert.alert(
        "Call Driver",
        `Driver's phone number: ${rideStatus.driver_phone}`,
        [
          { text: "Close", style: "cancel" },
          { 
            text: "Copy Number", 
            onPress: () => {
              // Copy to clipboard - works on all platforms
              const phoneNumber = rideStatus.driver_phone || "";
              if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(phoneNumber).then(() => {
                  Alert.alert("Copied!", "Phone number copied to clipboard");
                }).catch(() => {
                  Alert.alert("Info", `Phone: ${phoneNumber}`);
                });
              } else {
                Alert.alert("Info", `Phone: ${phoneNumber}`);
              }
            } 
          },
        ]
      );
    } else {
      // On native platforms, use tel: link
      const phoneNumber = rideStatus.driver_phone || "";
      Linking.openURL(`tel:${phoneNumber}`).catch(() => {
        Alert.alert("Error", "Could not open phone dialer");
      });
    }
  };

  const renderTimeline = () => {
    const steps = [
      { id: "assigned", icon: "🚕", label: "Driver Assigned", active: true },
      { id: "on_way", icon: "🛣", label: "On the Way", active: rideStatus?.driver_progress === "ON_THE_WAY_TO_PICKUP" || rideStatus?.driver_progress === "ARRIVED_AT_PICKUP" || rideStatus?.driver_progress === "ON_THE_WAY_TO_DROPOFF" || rideStatus?.status === "IN_PROGRESS" },
      { id: "arrived", icon: "📍", label: "Arrived", active: rideStatus?.driver_progress === "ARRIVED_AT_PICKUP" || rideStatus?.driver_progress === "ON_THE_WAY_TO_DROPOFF" },
      { id: "completed", icon: "✅", label: "Completed", active: rideStatus?.status === "COMPLETED" },
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
    
    // Web-compatible confirmation
    if (Platform.OS === "web") {
      // @ts-ignore - window.confirm is available on web
      if (window.confirm("Are you sure you want to cancel this ride?")) {
        cancelRide(rideId).then((response: any) => {
          if (response.success) {
            alert("Your ride has been cancelled.");
            setRideId(null);
            setRideStatus(null);
            router.back();
          } else {
            alert(response.error || "Failed to cancel ride");
          }
        }).catch((error: any) => {
          alert("Failed to cancel ride: " + String(error));
        });
      }
      return;
    }

    Alert.alert(
      "Cancel Ride",
      "Are you sure you want to cancel this ride?",
      [
        { text: "No", style: "cancel" },
        { text: "Yes", onPress: async () => {
          try {
            const response = await cancelRide(rideId);
            if (response.success) {
              Alert.alert("Cancelled", "Your ride has been cancelled.", [
                { 
                  text: "OK",
                  onPress: () => {
                    setRideId(null);
                    setRideStatus(null);
                    router.back();
                  }
                }
              ]);
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

  const isCancelDisabled =
    rideStatus.status === "IN_PROGRESS" ||
    rideStatus.status === "COMPLETED" ||
    rideStatus.status === "CANCELLED";

  // Show feedback form if ride is completed but no feedback submitted
  if (rideStatus.status === "COMPLETED" && !rideStatus.passenger_feedback) {
    return (
      <RideFeedback
        rideId={rideStatus.ride_id}
        driverName={rideStatus.driver_name || "the driver"}
        onFeedbackSubmitted={() => {
          // Refresh the ride status to show feedback was submitted
          setRideStatus(prev => prev ? { ...prev, passenger_feedback: { submitted: true } } : null);
        }}
      />
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
        
        {rideStatus.status === "DRIVER_ASSIGNED" && rideStatus.pickup_otp && (
          <View style={[styles.driverInfo, { marginTop: 15, padding: 10, backgroundColor: "#FFF3E0", borderRadius: 8 }]}>
            <Text style={[styles.label, { color: "#F57C00", fontSize: 16 }]}>Start Ride OTP:</Text>
            <Text style={[styles.value, { color: "#E65100", fontSize: 24, fontWeight: "bold", letterSpacing: 4 }]}>{rideStatus.pickup_otp}</Text>
            <Text style={{ fontSize: 12, color: "#666", marginTop: 5 }}>Share this code with driver to start ride</Text>
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
            isCancelDisabled && styles.cancelButtonDisabled,
            pressed && styles.pressed,
          ]}
          onPress={handleCancelRide}
          disabled={isCancelDisabled}
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
  cancelButtonDisabled: {
    opacity: 0.5,
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
