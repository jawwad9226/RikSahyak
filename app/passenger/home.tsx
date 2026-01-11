import LocationInput from "@/src/components/LocationInput";
import { API_CONFIG } from "@/src/config/env";
import { useUser } from "@/src/context/UserContext";
import { createRideRequest, getRideStatus } from "@/src/services/api";
import { colors } from "@/src/utils/colors";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, Linking, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

interface LocationResult {
  name: string;
  latitude: number;
  longitude: number;
  category?: string;
  landmark?: string;
}

export default function PassengerHome() {
  const { user } = useUser();
  const router = useRouter();
  const [pickupLocation, setPickupLocation] = useState<LocationResult | null>(null);
  const [dropoffLocation, setDropoffLocation] = useState<LocationResult | null>(null);
  const [estimatedFare, setEstimatedFare] = useState<number | null>(null);
  const [distance, setDistance] = useState<number | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [distanceMethod, setDistanceMethod] = useState<string>("");
  const [rideId, setRideId] = useState<string | null>(null);
  const [rideStatus, setRideStatus] = useState<string | null>(null);
  const [statusLoading, setStatusLoading] = useState<boolean>(false);

  const handleCalculateFare = async () => {
    if (!pickupLocation || !dropoffLocation) {
      alert("Please select both pickup and dropoff locations");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_CONFIG.API_PREFIX}/rides/calculate-fare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pickup_location: pickupLocation.name,
          dropoff_location: dropoffLocation.name,
          pickup_coords: {
            latitude: pickupLocation.latitude,
            longitude: pickupLocation.longitude,
          },
          dropoff_coords: {
            latitude: dropoffLocation.latitude,
            longitude: dropoffLocation.longitude,
          },
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setEstimatedFare(data.estimated_fare);
        setDistance(data.distance_km);
        setEstimatedTime(data.estimated_time_minutes);
        setDistanceMethod(data.distance_method);
      } else {
        alert("Error calculating fare. Please try again.");
      }
    } catch (error) {
      alert("Error: " + error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookRide = () => {
    if (!estimatedFare) {
      alert("Calculate fare first");
      return;
    }
    if (!pickupLocation || !dropoffLocation) {
      alert("Please select pickup and dropoff locations");
      return;
    }

    // Minimal request to backend
    (async () => {
      try {
        setStatusLoading(true);
        const res = await createRideRequest({
          passenger_id: user?.user_id || "PAS-001",
          pickup_location: pickupLocation.name,
          dropoff_location: dropoffLocation.name,
          pickup_coords: {
            latitude: pickupLocation.latitude,
            longitude: pickupLocation.longitude,
          },
          dropoff_coords: {
            latitude: dropoffLocation.latitude,
            longitude: dropoffLocation.longitude,
          },
          estimated_fare: estimatedFare,
          distance_km: distance ?? 0,
        });
        if (res.success && res.data) {
          const data: any = res.data;
          setRideId(data.ride_id);
          setRideStatus(data.status || "REQUESTED");
        } else {
          alert("Failed to create ride request");
        }
      } catch (e: any) {
        const errorMessage = e?.message || String(e) || "Unknown error";
        alert("Error: " + errorMessage);
      } finally {
        setStatusLoading(false);
      }
    })();
  };

  const handleOpenInGoogleMaps = () => {
    if (!pickupLocation || !dropoffLocation) {
      alert("Select pickup and dropoff first");
      return;
    }
    const origin = `${pickupLocation.latitude},${pickupLocation.longitude}`;
    const destination = `${dropoffLocation.latitude},${dropoffLocation.longitude}`;
    const url = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&travelmode=driving`;
    Linking.openURL(url).catch(() => alert("Could not open Google Maps"));
  };

  // Poll ride status when we have a rideId
  useEffect(() => {
    if (!rideId) return;
    if (rideStatus === "COMPLETED") return;

    const interval = setInterval(async () => {
      try {
        const res = await getRideStatus(rideId);
        if (res.success && res.data) {
          const data: any = res.data;
          const status = data.status as string;
          if (status) {
            setRideStatus(status);
            
            // Navigate to active ride when driver accepts
            if (status === "DRIVER_ASSIGNED" || status === "IN_PROGRESS") {
              router.push("/passenger/active-ride");
            }
            
            if (status === "COMPLETED") {
              clearInterval(interval);
            }
          }
        }
      } catch (e) {
        // Silent: keep deterministic minimal behavior
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [rideId, rideStatus, router]);

  return (
    <>
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Where do you want to go?</Text>

      <LocationInput
        label="Pickup Location"
        placeholder="Search pickup location..."
        onSelect={setPickupLocation}
        currentValue={pickupLocation?.name || ""}
      />

      <LocationInput
        label="Dropoff Location"
        placeholder="Search dropoff location..."
        onSelect={setDropoffLocation}
        currentValue={dropoffLocation?.name || ""}
      />

      <Pressable
        style={({ pressed }) => [
          styles.calcButton,
          pressed && styles.pressed,
          (!pickupLocation || !dropoffLocation || loading) && styles.disabled,
        ]}
        onPress={handleCalculateFare}
        disabled={!pickupLocation || !dropoffLocation || loading}
      >
        <Text style={[styles.buttonText, { color: "#000" }]}>
          {loading ? "Calculating..." : "Calculate Fare"}
        </Text>
        {loading && <ActivityIndicator color="#000" style={{ marginLeft: 8 }} />}
      </Pressable>

      {estimatedFare && (
        <>
          <View style={styles.fareContainer}>
            <View style={styles.fareHeader}>
              <Text style={styles.fareLabel}>Estimated Fare</Text>
              <Text style={styles.fareAmount}>₹{estimatedFare}</Text>
            </View>

            <View style={styles.detailsRow}>
              <Text style={styles.detailLabel}>Distance:</Text>
              <Text style={styles.detailValue}>
                {distance?.toFixed(1)} km ({distanceMethod === "osrm" ? "Actual Route" : "Estimate"})
              </Text>
            </View>

            {estimatedTime && (
              <View style={styles.detailsRow}>
                <Text style={styles.detailLabel}>Est. Time:</Text>
                <Text style={styles.detailValue}>{estimatedTime} minutes</Text>
              </View>
            )}

            <View style={styles.breakdownRow}>
              <Text style={styles.breakdownLabel}>Base Fare: ₹20</Text>
              <Text style={styles.breakdownValue}>+ ₹{(estimatedFare - 20).toFixed(2)}</Text>
            </View>
          </View>

          <Pressable
            style={({ pressed }) => [styles.externalMapButton, pressed && styles.pressed]}
            onPress={handleOpenInGoogleMaps}
          >
            <Text style={styles.externalMapButtonText}>🗺️ Navigate with Google Maps</Text>
          </Pressable>
        </>
      )}

      {estimatedFare && (
        <Pressable
          style={({ pressed }) => [styles.bookButton, pressed && styles.pressed]}
          onPress={handleBookRide}
        >
          <Text style={[styles.buttonText, { color: "#FFC107" }]}>Book Ride Now</Text>
        </Pressable>
      )}

      {rideId && (
        <View style={styles.statusContainer}>
          <Text style={styles.statusTitle}>Ride Status</Text>
          <Text style={styles.statusText}>
            {statusLoading && !rideStatus ? "Requesting..." : rideStatus || "REQUESTED"}
          </Text>
          {rideStatus === "REQUESTED" && (
            <Text style={styles.statusHint}>Searching for a driver...</Text>
          )}
          {rideStatus === "DRIVER_ASSIGNED" && (
            <Text style={styles.statusHint}>Driver assigned. Ride will start soon.</Text>
          )}
          {rideStatus === "COMPLETED" && (
            <Text style={styles.statusHint}>Ride completed. Thank you!</Text>
          )}
        </View>
      )}

      <Text style={styles.disclaimer}>
        💡 Fares are calculated using real street routing for accuracy
      </Text>
    </ScrollView>
  </>
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
  calcButton: {
    backgroundColor: colors.primary,
    borderWidth: 2,
    borderColor: "#000",
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 10,
    flexDirection: "row",
    justifyContent: "center",
  },
  bookButton: {
    backgroundColor: "#000",
    borderWidth: 2,
    borderColor: colors.primary,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 15,
    marginBottom: 20,
  },
  buttonText: {
    fontSize: 18,
    fontWeight: "bold",
  },
  pressed: {
    opacity: 0.7,
  },
  disabled: {
    opacity: 0.5,
  },
  fareContainer: {
    backgroundColor: "#F5F5F5",
    padding: 15,
    borderRadius: 8,
    marginTop: 20,
    borderLeftWidth: 4,
    borderLeftColor: colors.primary,
  },
  fareHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#ddd",
  },
  fareLabel: {
    fontSize: 14,
    color: "#666",
    fontWeight: "500",
  },
  fareAmount: {
    fontSize: 28,
    fontWeight: "bold",
    color: colors.primary,
  },
  detailsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 13,
    color: "#666",
  },
  detailValue: {
    fontSize: 13,
    fontWeight: "600",
    color: "#000",
  },
  breakdownRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#ddd",
  },
  breakdownLabel: {
    fontSize: 12,
    color: "#666",
  },
  breakdownValue: {
    fontSize: 12,
    fontWeight: "bold",
    color: "#000",
  },
  disclaimer: {
    fontSize: 11,
    color: "#999",
    textAlign: "center",
    marginBottom: 20,
    fontStyle: "italic",
  },
  mapButton: {
    backgroundColor: "#4CAF50",
    borderWidth: 2,
    borderColor: "#000",
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 12,
  },
  mapButtonText: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#FFF",
  },
  externalMapButton: {
    backgroundColor: "#000",
    borderWidth: 2,
    borderColor: colors.primary,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 10,
  },
  externalMapButtonText: {
    fontSize: 16,
    fontWeight: "bold",
    color: colors.primary,
  },
  statusContainer: {
    backgroundColor: "#F9F9F9",
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#ddd",
    marginTop: 10,
  },
  statusTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
    marginBottom: 6,
  },
  statusText: {
    fontSize: 16,
    fontWeight: "700",
    color: colors.primary,
  },
  statusHint: {
    fontSize: 12,
    color: "#666",
    marginTop: 4,
  },
});
