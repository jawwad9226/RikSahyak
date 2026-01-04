import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

export default function Index() {
  const router = useRouter();

  const handleRoleSelect = (role: "driver" | "passenger" | "admin") => {
    router.push(`/${role}/home`);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>RikSahayak</Text>
      <Text style={styles.subtitle}>Auto Rickshaw Booking</Text>
      <Text style={styles.instruction}>Please Select your Role</Text>

      {/* Driver Button */}
      <Pressable
        style={({ pressed }) => [styles.button, styles.driverButton, pressed && styles.pressed]}
        onPress={() => handleRoleSelect("driver")}
      >
        <Text style={[styles.buttonText, styles.driverText]}>🚗 Driver</Text>
      </Pressable>

      {/* Passenger Button */}
      <Pressable
        style={({ pressed }) => [styles.button, styles.passengerButton, pressed && styles.pressed]}
        onPress={() => handleRoleSelect("passenger")}
      >
        <Text style={[styles.buttonText, styles.passengerText]}>👤 Passenger</Text>
      </Pressable>

      {/* Admin Button */}
      <Pressable
        style={({ pressed }) => [styles.button, styles.adminButton, pressed && styles.pressed]}
        onPress={() => handleRoleSelect("admin")}
      >
        <Text style={[styles.buttonText, styles.adminText]}>📊 Admin</Text>
      </Pressable>
    </View>
  );
}
const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#FFF",
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 36,
    fontWeight: "bold",
    color: "#FFC107",
    marginBottom: 5,
    textShadowColor: "#000",
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 3,
  },
  subtitle: {
    fontSize: 16,
    color: "#666",
    marginBottom: 30,
    fontStyle: "italic",
  },
  instruction: {
    fontSize: 18,
    fontWeight: "600",
    color: "#000",
    marginBottom: 25,
    textAlign: "center",
  },
  button: {
    width: "100%",
    paddingVertical: 16,
    marginVertical: 10,
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 2,
    borderColor: "#000",
  },
  driverButton: {
    backgroundColor: "#FFC107",
    borderColor: "#000",
  },
  passengerButton: {
    backgroundColor: "#000",
    borderColor: "#FFC107",
  },
  adminButton: {
    backgroundColor: "#333",
    borderColor: "#FFC107",
  },
  buttonText: {
    fontSize: 18,
    fontWeight: "bold",
  },
  driverText: {
    color: "#000",
  },
  passengerText: {
    color: "#FFC107",
  },
  adminText: {
    color: "#FFC107",
  },
  pressed: {
    opacity: 0.7,
  },
});