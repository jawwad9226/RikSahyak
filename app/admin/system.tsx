import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet, ScrollView, RefreshControl } from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { apiGet } from "@/src/services/apiClient";

const Colors = {
  primary: "#FFC107",
  background: "#FFF",
  surface: "#F5F5F5",
  text: "#000",
  textSecondary: "#666",
};

export default function SystemHealthScreen() {
  const [health, setHealth] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSystemData = async () => {
    setLoading(true);
    try {
      const [healthRes, logsRes] = await Promise.all([
        apiGet("/admin/system/health"),
        apiGet("/admin/system/logs?lines=50"),
      ]);

      if (healthRes.success) setHealth(healthRes.data);
      if (logsRes.success) setLogs(logsRes.data.logs || []);
    } catch (err) {
      console.error("Failed to fetch system data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemData();
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchSystemData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={fetchSystemData} tintColor={Colors.primary} />}
    >
      <Text style={styles.headerTitle}>System & Machine Health</Text>

      <View style={styles.cardsContainer}>
        {/* Battery Card */}
        <View style={styles.card}>
          <MaterialCommunityIcons name="battery-high" size={32} color="#4CAF50" />
          <Text style={styles.cardTitle}>Battery</Text>
          <Text style={styles.cardValue}>{health?.battery_percent ? `${health.battery_percent}%` : "Loading..."}</Text>
        </View>

        {/* CPU Temp Card */}
        <View style={styles.card}>
          <MaterialCommunityIcons name="thermometer" size={32} color="#F44336" />
          <Text style={styles.cardTitle}>CPU Temp</Text>
          <Text style={styles.cardValue}>{health?.cpu_temperature || "Loading..."}</Text>
        </View>

        {/* Memory Card */}
        <View style={styles.card}>
          <MaterialCommunityIcons name="memory" size={32} color="#2196F3" />
          <Text style={styles.cardTitle}>Memory</Text>
          <Text style={styles.cardValue}>{health?.ram_usage || "Loading..."}</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Live PM2 / Server Logs</Text>
      <View style={styles.terminalContainer}>
        {logs.length === 0 ? (
          <Text style={styles.terminalText}>No logs available or server is starting...</Text>
        ) : (
          logs.map((line, idx) => (
            <Text key={idx} style={styles.terminalText}>{line}</Text>
          ))
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    padding: 16,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "bold",
    color: Colors.text,
    marginBottom: 20,
    marginTop: 10,
  },
  cardsContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 24,
  },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    width: "30%",
    elevation: 3,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardTitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginTop: 8,
    marginBottom: 4,
  },
  cardValue: {
    fontSize: 18,
    fontWeight: "bold",
    color: Colors.text,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "bold",
    color: Colors.text,
    marginBottom: 12,
  },
  terminalContainer: {
    backgroundColor: "#1E1E1E",
    borderRadius: 8,
    padding: 16,
    minHeight: 300,
    marginBottom: 40,
  },
  terminalText: {
    fontFamily: "monospace",
    color: "#00FF00",
    fontSize: 12,
    marginBottom: 4,
  },
});
