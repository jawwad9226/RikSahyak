import { RoleSelectionModal } from "@/src/components/RoleSelectionModal";
import { useUser } from "@/src/context/UserContext";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";

export default function Index() {
  const router = useRouter();
  const { user, loading, setUser } = useUser();
  const [showModal, setShowModal] = useState(false);

  // If user is already set, navigate to their role screen
  useEffect(() => {
    if (!loading && user) {
      router.replace(`/${user.role}`);
    } else if (!loading && !user) {
      setShowModal(true);
    }
  }, [user, loading]);

  const handleSelectUser = async (selected: { user_id: string; name?: string; role: "passenger" | "driver" | "admin" }) => {
    await setUser(selected);
    setShowModal(false);
    router.replace(`/${selected.role}`);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <>
      <RoleSelectionModal visible={showModal} onSelect={handleSelectUser} />
    </>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#FFF",
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