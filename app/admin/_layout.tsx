import { useUser } from "@/src/context/UserContext";
import { Stack, useRouter } from "expo-router";
import { Text, TouchableOpacity } from "react-native";

export default function AdminLayout() {
  const router = useRouter();
  const { logout } = useUser();

  const handleLogout = async () => {
    await logout();
    router.replace("/");
  };

  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: "#333",
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
      <Stack.Screen name="dashboard" options={{ title: "Admin Dashboard" }} />
      <Stack.Screen name="users" options={{ title: "User Management" }} />
      <Stack.Screen name="rides" options={{ title: "Ride Management" }} />
      <Stack.Screen name="analytics" options={{ title: "Analytics" }} />
      <Stack.Screen name="settings" options={{ title: "System Settings" }} />
    </Stack>
  );
}
