import { Stack } from "expo-router";

export default function DriverLayout() {
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
      }}
    >
      <Stack.Screen name="home" options={{ title: "Available Rides" }} />
      <Stack.Screen name="current-ride" options={{ title: "Current Ride" }} />
      <Stack.Screen name="earnings" options={{ title: "Today's Earnings" }} />
    </Stack>
  );
}
