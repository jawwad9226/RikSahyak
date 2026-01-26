import { apiGet, apiPost } from "@/src/services/api";
import { useEffect, useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from "react-native";

interface SystemSettings {
  max_ride_distance_km: number;
  base_fare: number;
  per_km_rate: number;
  per_minute_rate: number;
  surge_multiplier: number;
  maintenance_mode: boolean;
  otp_expiry_minutes: number;
  max_active_rides_per_driver: number;
  driver_search_radius_km: number;
  passenger_pickup_radius_km: number;
}

export default function Settings() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [editedSettings, setEditedSettings] = useState<Partial<SystemSettings>>({});

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setIsLoading(true);
      const response = await apiGet<SystemSettings>("/admin/settings");
      if (response.success && response.data) {
        setSettings(response.data);
        setEditedSettings(response.data);
      }
    } catch (error) {
      console.error("Failed to fetch settings:", error);
      Alert.alert("Error", "Failed to load settings");
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setIsSaving(true);
      const response = await apiPost("/admin/settings", editedSettings);
      if (response.success) {
        setSettings(editedSettings as SystemSettings);
        Alert.alert("Success", "Settings saved successfully");
      } else {
        Alert.alert("Error", "Failed to save settings");
      }
    } catch (error) {
      console.error("Failed to save settings:", error);
      Alert.alert("Error", "Failed to save settings");
    } finally {
      setIsSaving(false);
    }
  };

  const updateSetting = (key: keyof SystemSettings, value: any) => {
    setEditedSettings(prev => ({ ...prev, [key]: value }));
  };

  const resetSettings = () => {
    if (settings) {
      setEditedSettings(settings);
    }
  };

  const renderNumberInput = (
    label: string,
    key: keyof SystemSettings,
    min?: number,
    max?: number,
    step: number = 1
  ) => (
    <View style={styles.settingRow}>
      <Text style={styles.settingLabel}>{label}</Text>
      <TextInput
        style={styles.numberInput}
        value={editedSettings[key]?.toString() || ""}
        onChangeText={(text) => {
          const numValue = parseFloat(text);
          if (!isNaN(numValue) && (!min || numValue >= min) && (!max || numValue <= max)) {
            updateSetting(key, numValue);
          }
        }}
        keyboardType="numeric"
        placeholder={settings?.[key]?.toString() || "0"}
      />
    </View>
  );

  const renderSwitch = (label: string, key: keyof SystemSettings) => (
    <View style={styles.settingRow}>
      <Text style={styles.settingLabel}>{label}</Text>
      <Switch
        value={editedSettings[key] as boolean || false}
        onValueChange={(value) => updateSetting(key, value)}
        trackColor={{ false: "#767577", true: "#81b0ff" }}
        thumbColor={editedSettings[key] ? "#f5dd4b" : "#f4f3f4"}
      />
    </View>
  );

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Settings</Text>
        <Text style={styles.loadingText}>Loading settings...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>System Settings</Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Pricing Configuration</Text>

        {renderNumberInput("Base Fare (₹)", "base_fare", 0)}
        {renderNumberInput("Per KM Rate (₹)", "per_km_rate", 0)}
        {renderNumberInput("Per Minute Rate (₹)", "per_minute_rate", 0)}
        {renderNumberInput("Surge Multiplier", "surge_multiplier", 1, 5, 0.1)}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Ride Limits</Text>

        {renderNumberInput("Max Ride Distance (KM)", "max_ride_distance_km", 1, 100)}
        {renderNumberInput("Max Active Rides per Driver", "max_active_rides_per_driver", 1, 10)}
        {renderNumberInput("Driver Search Radius (KM)", "driver_search_radius_km", 1, 50)}
        {renderNumberInput("Passenger Pickup Radius (KM)", "passenger_pickup_radius_km", 0.1, 5, 0.1)}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Security & OTP</Text>

        {renderNumberInput("OTP Expiry (Minutes)", "otp_expiry_minutes", 1, 60)}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>System Control</Text>

        {renderSwitch("Maintenance Mode", "maintenance_mode")}
      </View>

      <View style={styles.buttonContainer}>
        <Pressable
          style={[styles.button, styles.saveButton]}
          onPress={saveSettings}
          disabled={isSaving}
        >
          <Text style={styles.saveButtonText}>
            {isSaving ? "Saving..." : "Save Settings"}
          </Text>
        </Pressable>

        <Pressable
          style={[styles.button, styles.resetButton]}
          onPress={resetSettings}
        >
          <Text style={styles.resetButtonText}>Reset Changes</Text>
        </Pressable>
      </View>

      <View style={styles.warningSection}>
        <Text style={styles.warningTitle}>⚠️ Important Notes</Text>
        <Text style={styles.warningText}>
          • Changes to pricing will affect new ride requests immediately
        </Text>
        <Text style={styles.warningText}>
          • Maintenance mode will prevent new ride requests
        </Text>
        <Text style={styles.warningText}>
          • OTP expiry changes only affect new OTPs
        </Text>
        <Text style={styles.warningText}>
          • Ride limits are enforced for new assignments
        </Text>
      </View>
    </ScrollView>
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
  loadingText: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
  },
  section: {
    backgroundColor: "#F9F9F9",
    borderRadius: 8,
    padding: 15,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: "#E0E0E0",
    paddingBottom: 5,
  },
  settingRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#F0F0F0",
  },
  settingLabel: {
    fontSize: 16,
    color: "#333",
    flex: 1,
  },
  numberInput: {
    borderWidth: 1,
    borderColor: "#DDD",
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 16,
    width: 100,
    textAlign: "right",
    backgroundColor: "#FFF",
  },
  buttonContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 30,
  },
  button: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
    marginHorizontal: 5,
  },
  saveButton: {
    backgroundColor: "#4CAF50",
  },
  saveButtonText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "bold",
  },
  resetButton: {
    backgroundColor: "#F5F5F5",
    borderWidth: 1,
    borderColor: "#DDD",
  },
  resetButtonText: {
    color: "#666",
    fontSize: 16,
    fontWeight: "500",
  },
  warningSection: {
    backgroundColor: "#FFF3CD",
    borderRadius: 8,
    padding: 15,
    borderWidth: 1,
    borderColor: "#FFEAA7",
  },
  warningTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#856404",
    marginBottom: 10,
  },
  warningText: {
    fontSize: 14,
    color: "#856404",
    marginBottom: 5,
    lineHeight: 20,
  },
});