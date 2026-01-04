 import LocationInput from "@/src/components/LocationInput";
import LocationMap from "@/src/components/LocationMap";
import { colors } from "@/src/utils/colors";
import { useState } from "react";
import { ActivityIndicator, Linking, Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

interface LocationResult {
  name: string;
  latitude: number;
  longitude: number;
  category?: string;
  landmark?: string;
}

export default function PassengerHome() {
  const [pickupLocation, setPickupLocation] = useState<LocationResult | null>(null);
  const [dropoffLocation, setDropoffLocation] = useState<LocationResult | null>(null);
  const [estimatedFare, setEstimatedFare] = useState<number | null>(null);
  const [distance, setDistance] = useState<number | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [showMap, setShowMap] = useState(false);
  const [distanceMethod, setDistanceMethod] = useState<string>("");

  const handleCalculateFare = async () => {
    if (!pickupLocation || !dropoffLocation) {
      alert("Please select both pickup and dropoff locations");
      return;
    }

    setLoading(true);
    try {
      const API_URL = "http://192.168.2.6:8000";
      
      const response = await fetch(`${API_URL}/api/v1/rides/calculate-fare`, {
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
    alert(
      `Booking ride from ${pickupLocation?.name} to ${dropoffLocation?.name}\nFare: ₹${estimatedFare}`
    );
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
            style={({ pressed }) => [styles.mapButton, pressed && styles.pressed]}
            onPress={() => setShowMap(true)}
          >
            <Text style={styles.mapButtonText}>🗺️ View Route on Map</Text>
          </Pressable>

          <Pressable
            style={({ pressed }) => [styles.externalMapButton, pressed && styles.pressed]}
            onPress={handleOpenInGoogleMaps}
          >
            <Text style={styles.externalMapButtonText}>Open in Google Maps (Navigation)</Text>
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

      <Text style={styles.disclaimer}>
        💡 Fares are calculated using real street routing for accuracy
      </Text>
    </ScrollView>

    <Modal visible={showMap} animationType="slide" onRequestClose={() => setShowMap(false)}>
      {(pickupLocation && dropoffLocation && typeof pickupLocation.latitude === 'number' && typeof dropoffLocation.latitude === 'number') ? (
          <LocationMap
            pickup={pickupLocation ? {
              latitude: pickupLocation.latitude,
              longitude: pickupLocation.longitude,
              name: pickupLocation.name,
            } : undefined}
            dropoff={dropoffLocation ? {
              latitude: dropoffLocation.latitude,
              longitude: dropoffLocation.longitude,
              name: dropoffLocation.name,
            } : undefined}
            distance={distance || undefined}
            showDistance={true}
            onClose={() => setShowMap(false)}
          />
      ) : (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <Text style={{ color: 'red', fontSize: 16 }}>Invalid location data. Please select both locations again.</Text>
          <Pressable onPress={() => setShowMap(false)} style={{ marginTop: 20 }}>
            <Text style={{ color: colors.primary, fontWeight: 'bold' }}>Close</Text>
          </Pressable>
        </View>
      )}
    </Modal>
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
});
