import { Stack } from "expo-router";

export default function PassengerLayout() {
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
      }}
    >
      <Stack.Screen name="home" options={{ title: "Book a Ride" }} />
      <Stack.Screen name="active-ride" options={{ title: "Active Ride" }} />
      <Stack.Screen name="history" options={{ title: "Ride History" }} />
    </Stack>
  );
}
