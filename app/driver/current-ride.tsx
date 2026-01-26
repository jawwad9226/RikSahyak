import { API_CONFIG } from "@/src/config/env";
import { useUser } from "@/src/context/UserContext";
import { getRideStatus, startRide, updateDriverProgress } from "@/src/services/api";
import { useEffect, useState } from "react";
import { Alert, Linking, Modal, Platform, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

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
  pickup_otp?: string;
}

// Progress states
type ProgressState = "NOT_STARTED" | "ON_THE_WAY_TO_PICKUP" | "ARRIVED_AT_PICKUP" | "ON_THE_WAY_TO_DROPOFF";

export default function CurrentRide() {
  const { user } = useUser();
  const [currentRide, setCurrentRide] = useState<CurrentRide | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [rideId, setRideId] = useState<string | null>(null);
  const [isUpdatingProgress, setIsUpdatingProgress] = useState(false);
  
  // OTP Modal State
  const [isOtpModalVisible, setIsOtpModalVisible] = useState(false);
  const [otpInput, setOtpInput] = useState("");
  const [isSubmittingOtp, setIsSubmittingOtp] = useState(false);

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
            pickup_otp: data.pickup_otp,
          });
        }
      } catch (error) {
        console.error("Error fetching ride details:", error);
      }
    };

    fetchRideDetails();

    // Poll for updates every 10 seconds (reduced frequency to prevent excessive API calls)
    const interval = setInterval(fetchRideDetails, 10000);
    return () => clearInterval(interval);
  }, [rideId]);

  const handleStartRide = async () => {
    // Open OTP Modal if status is DRIVER_ASSIGNED
    if (currentRide?.status === "DRIVER_ASSIGNED") {
      setOtpInput("");
      setIsOtpModalVisible(true);
    } else {
      // Fallback for direct start if already in progress or other states (unlikely)
      Alert.alert("Error", "Ride already started or invalid state.");
    }
  };
  
  const submitOtp = async () => {
    if (!rideId || !otpInput || otpInput.length !== 4) {
      Alert.alert("Invalid input", "Please enter a valid 4-digit OTP.");
      return;
    }
    
    setIsSubmittingOtp(true);
    try {
      const response = await startRide(rideId, user?.user_id, otpInput);
      if (response.success) {
        setIsOtpModalVisible(false);
        setOtpInput("");
        Alert.alert("Success", "Ride completed successfully!");
        if (currentRide) {
          setCurrentRide({ ...currentRide, status: "COMPLETED" });
        }
      } else {
        Alert.alert("Error", response.error || "Failed to complete ride. Check OTP.");
      }
    } catch (error) {
      Alert.alert("Error", "Failed to start ride: " + String(error));
    } finally {
      setIsSubmittingOtp(false);
    }
  };

  const handleCallPassenger = () => {
    if (!currentRide?.passenger_phone) {
      Alert.alert("Error", "Passenger phone number not available");
      return;
    }

    if (Platform.OS === "web") {
      // On web, show an alert with the phone number
      Alert.alert(
        "Call Passenger",
        `Passenger's phone number: ${currentRide.passenger_phone}`,
        [
          { text: "Close", style: "cancel" },
          { 
            text: "Copy Number", 
            onPress: () => {
              // Copy to clipboard on web (if available)
              if (navigator.clipboard) {
                navigator.clipboard.writeText(currentRide.passenger_phone)
                  .then(() => Alert.alert("Copied", "Phone number copied to clipboard."))
                  .catch(() => Alert.alert("Error", "Could not copy to clipboard."));
              } else {
                Alert.alert("Not Supported", "Clipboard API not available in this browser.");
              }
            } 
          },
        ]
      );
    } else {
      // On native platforms, use tel: link
      Linking.openURL(`tel:${currentRide.passenger_phone}`);
    }
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
          Status: {currentRide.status === "DRIVER_ASSIGNED" ? "Waiting for Pickup" :
                   currentRide.status === "IN_PROGRESS" ? "In Progress" :
                   currentRide.status}
        </Text>
      </View>

      {/* Driver Progress Display */}
      {currentRide.status !== "COMPLETED" && currentRide.status !== "CANCELLED" && (
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
        {currentRide.status !== "COMPLETED" && currentRide.status !== "CANCELLED" && (
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

        {currentRide.status === "DRIVER_ASSIGNED" && (
          <Pressable
            style={({ pressed }) => [
              styles.startButton,
              pressed && styles.pressed,
            ]}
            onPress={handleStartRide}
          >
            <Text style={styles.startButtonText}>Verify & Complete</Text>
          </Pressable>
        )}

        {currentRide.status === "COMPLETED" && (
          <View style={styles.completedContainer}>
            <Text style={styles.completedText}>✅ Ride Completed</Text>
            <Text style={styles.completedSubtext}>Waiting for passenger feedback</Text>
          </View>
        )}
      </View>

      {/* OTP Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={isOtpModalVisible}
        onRequestClose={() => setIsOtpModalVisible(false)}
        accessible={true}
        accessibilityViewIsModal={true}
      >
        <View style={styles.centeredView} accessible={true}>
          <Pressable 
            style={styles.backdrop} 
            onPress={() => setIsOtpModalVisible(false)}
            accessible={false}
          />
          <View style={styles.modalView} accessible={true}>
            <Text style={styles.modalTitle}>Enter OTP</Text>
            <Text style={styles.modalSubtitle}>Ask passenger for the 4-digit code to complete ride</Text>
            
            <TextInput
              style={styles.otpInput}
              onChangeText={setOtpInput}
              value={otpInput}
              placeholder="0000"
              keyboardType="number-pad"
              maxLength={4}
              autoFocus={true}
            />

            <View style={styles.modalButtons}>
              <Pressable
                style={[styles.modalBtn, styles.cancelBtn]}
                onPress={() => setIsOtpModalVisible(false)}
              >
                <Text style={styles.modalBtnText}>Cancel</Text>
              </Pressable>
              
              <Pressable
                style={[styles.modalBtn, styles.submitBtn, isSubmittingOtp && styles.btnDisabled]}
                onPress={submitOtp}
                disabled={isSubmittingOtp}
              >
                <Text style={[styles.modalBtnText, {color: 'white'}]}>
                  {isSubmittingOtp ? "Verifying..." : "Complete Ride"}
                </Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  // Modal Styles
  centeredView: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "rgba(0,0,0,0.5)",
  },
  backdrop: {
    position: 'absolute' as any,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  modalView: {
    margin: 20,
    backgroundColor: "white",
    borderRadius: 20,
    padding: 35,
    alignItems: "center",
    boxShadow: "0px 2px 4px rgba(0,0,0,0.25)",
    elevation: 5,
    width: '80%',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 10,
  },
  modalSubtitle: {
    fontSize: 14,
    color: "#666",
    marginBottom: 20,
    textAlign: "center",
  },
  otpInput: {
    height: 50,
    width: '100%',
    borderColor: '#ddd',
    borderWidth: 1,
    borderRadius: 8,
    fontSize: 24,
    textAlign: 'center',
    marginBottom: 20,
    letterSpacing: 8,
    fontWeight: 'bold',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
  },
  modalBtn: {
    borderRadius: 8,
    padding: 12,
    elevation: 2,
    minWidth: '45%',
    alignItems: 'center',
  },
  cancelBtn: {
    backgroundColor: '#f5f5f5',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  submitBtn: {
    backgroundColor: '#FFC107',
  },
  btnDisabled: {
    backgroundColor: '#ccc',
  },
  modalBtnText: {
    fontWeight: "bold",
    color: '#333',
  },
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
  completedContainer: {
    alignItems: "center",
    padding: 20,
    backgroundColor: "#E8F5E8",
    borderRadius: 8,
    marginTop: 10,
  },
  completedText: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#2E7D32",
    marginBottom: 5,
  },
  completedSubtext: {
    fontSize: 14,
    color: "#666",
  },
});
