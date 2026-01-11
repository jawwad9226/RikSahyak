import { useUser } from "@/src/context/UserContext";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Stack, useRouter } from "expo-router";
import { Text, TouchableOpacity } from "react-native";

export default function DriverLayout() {
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
          backgroundColor: "#000",
        },
        headerTintColor: "#FFC107",
        headerTitleStyle: {
          fontWeight: "bold",
          color: "#FFC107",
        },
        headerRight: () => (
          <TouchableOpacity onPress={handleLogout} style={{ marginRight: 10 }}>
            <Text style={{ color: "#FFC107", fontWeight: "bold" }}>Logout</Text>
          </TouchableOpacity>
        ),
      }}
    >
      <Stack.Screen name="home" options={{ title: "Available Rides" }} />
      <Stack.Screen name="current-ride" options={{ title: "Current Ride" }} />
      <Stack.Screen name="earnings" options={{ title: "Today's Earnings" }} />
    </Stack>
  );
}
