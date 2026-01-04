import { Stack } from "expo-router";

export default function AdminLayout() {
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
      }}
    >
      <Stack.Screen name="dashboard" options={{ title: "Admin Dashboard" }} />
    </Stack>
  );
}
