import { useUser } from "@/src/context/UserContext";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Stack, useRouter } from "expo-router";
import { Text, TouchableOpacity } from "react-native";

export default function PassengerLayout() {
  const router = useRouter();
  const { logout } = useUser();

  const handleLogout = async () => {
    // Clear AsyncStorage keys
    await AsyncStorage.multiRemove(["@user", "riksahyak:queuedRequests"]);
    // Update context state
    await logout();
    // Navigate to role selection
    router.replace("/");
  };

  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: "#FFC107",
        },
        headerTintColor: "#000",
        headerTitleStyle: {
          fontWeight: "bold",
        },
        headerRight: () => (
          <TouchableOpacity onPress={handleLogout} style={{ marginRight: 10 }}>
            <Text style={{ color: "#000", fontWeight: "bold" }}>Logout</Text>
          </TouchableOpacity>
        ),
      }}
    >
      <Stack.Screen name="home" options={{ title: "Book a Ride" }} />
      <Stack.Screen name="active-ride" options={{ title: "Active Ride" }} />
      <Stack.Screen name="history" options={{ title: "Ride History" }} />
    </Stack>
  );
}
