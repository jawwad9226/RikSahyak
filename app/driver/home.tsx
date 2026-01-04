import { useState } from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";

interface RideRequest {
  id: string;
  pickup: string;
  dropoff: string;
  fare: number;
  distance: number;
}

export default function DriverHome() {
  const [rideRequests, setRideRequests] = useState<RideRequest[]>([
    {
      id: "1",
      pickup: "Malkapur Station",
      dropoff: "Civil Lines",
      fare: 65,
      distance: 3.2,
    },
    {
      id: "2",
      pickup: "Bus Stand",
      dropoff: "Hospital",
      fare: 45,
      distance: 2.1,
    },
  ]);

  const handleAcceptRide = (rideId: string) => {
    alert(`Ride ${rideId} accepted!`);
    // TODO: Update Firebase with accepted ride
  };

  const renderRideCard = ({ item }: { item: RideRequest }) => (
    <View style={styles.rideCard}>
      <View style={styles.rideInfo}>
        <Text style={styles.location}>{item.pickup}</Text>
        <Text style={styles.arrow}>↓</Text>
        <Text style={styles.location}>{item.dropoff}</Text>
        <View style={styles.detailsRow}>
          <Text style={styles.detail}>{item.distance} km</Text>
          <Text style={styles.fareAmount}>₹{item.fare}</Text>
        </View>
      </View>
      <Pressable
        style={({ pressed }) => [
          styles.acceptButton,
          pressed && styles.pressed,
        ]}
        onPress={() => handleAcceptRide(item.id)}
      >
        <Text style={styles.acceptText}>Accept</Text>
      </Pressable>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Available Ride Requests</Text>
      <FlatList
        data={rideRequests}
        renderItem={renderRideCard}
        keyExtractor={(item) => item.id}
        scrollEnabled={true}
      />
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
  rideCard: {
    backgroundColor: "#F9F9F9",
    borderWidth: 2,
    borderColor: "#FFC107",
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
  },
  arrow: {
    fontSize: 14,
    color: "#666",
    marginVertical: 2,
  },
  detailsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 10,
  },
  detail: {
    fontSize: 14,
    color: "#666",
  },
  fareAmount: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#FFC107",
  },
  acceptButton: {
    backgroundColor: "#FFC107",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 6,
    marginLeft: 10,
  },
  acceptText: {
    fontSize: 14,
    fontWeight: "bold",
    color: "#000",
  },
  pressed: {
    opacity: 0.8,
  },
});
