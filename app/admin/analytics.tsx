import { apiGet } from "@/src/services/api";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

interface AnalyticsData {
  period_days: number;
  daily_stats: Record<string, { rides: number; revenue: number }>;
  revenue_by_hour: Record<string, number>;
  rides_by_status: Record<string, number>;
  total_revenue_period: number;
  total_rides_period: number;
}

export default function Analytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  useEffect(() => {
    fetchAnalytics();
  }, [selectedPeriod]);

  const fetchAnalytics = async () => {
    try {
      setIsLoading(true);
      const response = await apiGet<AnalyticsData>(`/admin/analytics?days=${selectedPeriod}`);
      if (response.success && response.data) {
        setAnalytics(response.data);
      }
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const periods = [7, 30, 90];

  const renderBarChart = (data: Record<string, number>, title: string, color: string) => {
    const maxValue = Math.max(...Object.values(data));
    const sortedKeys = Object.keys(data).sort();

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>{title}</Text>
        {sortedKeys.map((key) => {
          const value = data[key];
          const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;

          return (
            <View key={key} style={styles.barRow}>
              <Text style={styles.barLabel}>{key}</Text>
              <View style={styles.barContainer}>
                <View
                  style={[
                    styles.bar,
                    { width: `${percentage}%`, backgroundColor: color }
                  ]}
                />
                <Text style={styles.barValue}>{value}</Text>
              </View>
            </View>
          );
        })}
      </View>
    );
  };

  const renderDailyStats = () => {
    if (!analytics?.daily_stats) return null;

    const sortedDates = Object.keys(analytics.daily_stats).sort();
    const maxRides = Math.max(...sortedDates.map(date => analytics.daily_stats[date].rides));

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Daily Performance (Last {selectedPeriod} Days)</Text>
        {sortedDates.map((date) => {
          const stats = analytics.daily_stats[date];
          const ridesPercentage = maxRides > 0 ? (stats.rides / maxRides) * 100 : 0;

          return (
            <View key={date} style={styles.dailyRow}>
              <Text style={styles.dateLabel}>
                {new Date(date).toLocaleDateString()}
              </Text>
              <View style={styles.dailyStats}>
                <View style={styles.dailyBarContainer}>
                  <View
                    style={[
                      styles.dailyBar,
                      { width: `${ridesPercentage}%`, backgroundColor: "#2196F3" }
                    ]}
                  />
                  <Text style={styles.dailyValue}>{stats.rides} rides</Text>
                </View>
                <Text style={styles.revenueText}>₹{stats.revenue}</Text>
              </View>
            </View>
          );
        })}
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Analytics</Text>
        <Text style={styles.loadingText}>Loading analytics...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Analytics Dashboard</Text>

      <View style={styles.periodSelector}>
        <Text style={styles.periodLabel}>Time Period:</Text>
        <View style={styles.periodButtons}>
          {periods.map((period) => (
            <Pressable
              key={period}
              style={[styles.periodButton, selectedPeriod === period && styles.activePeriod]}
              onPress={() => setSelectedPeriod(period)}
            >
              <Text style={[styles.periodText, selectedPeriod === period && styles.activePeriodText]}>
                {period} Days
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      <View style={styles.summaryCards}>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryValue}>{analytics?.total_rides_period || 0}</Text>
          <Text style={styles.summaryLabel}>Total Rides</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryValue}>₹{analytics?.total_revenue_period || 0}</Text>
          <Text style={styles.summaryLabel}>Total Revenue</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryValue}>
            ₹{analytics?.total_rides_period ?
              Math.round((analytics.total_revenue_period / analytics.total_rides_period) * 100) / 100 : 0}
          </Text>
          <Text style={styles.summaryLabel}>Avg. Fare</Text>
        </View>
      </View>

      {renderDailyStats()}

      {analytics?.revenue_by_hour && renderBarChart(
        analytics.revenue_by_hour,
        "Revenue by Hour",
        "#4CAF50"
      )}

      {analytics?.rides_by_status && renderBarChart(
        analytics.rides_by_status,
        "Rides by Status",
        "#FFC107"
      )}

      <View style={styles.insightsContainer}>
        <Text style={styles.sectionTitle}>Key Insights</Text>

        <View style={styles.insightCard}>
          <Text style={styles.insightTitle}>Peak Hours</Text>
          <Text style={styles.insightText}>
            {analytics?.revenue_by_hour ?
              `Highest revenue at ${Object.keys(analytics.revenue_by_hour)
                .reduce((a, b) => analytics.revenue_by_hour[a] > analytics.revenue_by_hour[b] ? a : b)}:00` :
              "No data available"}
          </Text>
        </View>

        <View style={styles.insightCard}>
          <Text style={styles.insightTitle}>Completion Rate</Text>
          <Text style={styles.insightText}>
            {analytics?.rides_by_status ?
              `${Math.round((analytics.rides_by_status.COMPLETED /
                Object.values(analytics.rides_by_status).reduce((a, b) => a + b, 0)) * 100)}% of rides completed` :
              "No data available"}
          </Text>
        </View>

        <View style={styles.insightCard}>
          <Text style={styles.insightTitle}>Daily Average</Text>
          <Text style={styles.insightText}>
            {analytics?.total_rides_period ?
              `${Math.round(analytics.total_rides_period / selectedPeriod)} rides per day` :
              "No data available"}
          </Text>
        </View>
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
  periodSelector: {
    marginBottom: 20,
  },
  periodLabel: {
    fontSize: 16,
    fontWeight: "500",
    color: "#000",
    marginBottom: 10,
  },
  periodButtons: {
    flexDirection: "row",
  },
  periodButton: {
    backgroundColor: "#F5F5F5",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 10,
  },
  activePeriod: {
    backgroundColor: "#FFC107",
  },
  periodText: {
    fontSize: 14,
    color: "#666",
  },
  activePeriodText: {
    color: "#000",
    fontWeight: "500",
  },
  summaryCards: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 20,
  },
  summaryCard: {
    backgroundColor: "#F5F5F5",
    padding: 15,
    borderRadius: 8,
    alignItems: "center",
    width: "31%",
  },
  summaryValue: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#000",
  },
  summaryLabel: {
    fontSize: 12,
    color: "#666",
    marginTop: 5,
    textAlign: "center",
  },
  chartContainer: {
    backgroundColor: "#F9F9F9",
    borderRadius: 8,
    padding: 15,
    marginBottom: 20,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 15,
  },
  barRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
  },
  barLabel: {
    fontSize: 14,
    color: "#666",
    width: 40,
    textAlign: "right",
    marginRight: 10,
  },
  barContainer: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
  },
  bar: {
    height: 20,
    borderRadius: 4,
    marginRight: 10,
  },
  barValue: {
    fontSize: 12,
    color: "#666",
    minWidth: 30,
  },
  dailyRow: {
    marginBottom: 12,
  },
  dateLabel: {
    fontSize: 14,
    color: "#666",
    marginBottom: 4,
  },
  dailyStats: {
    flexDirection: "row",
    alignItems: "center",
  },
  dailyBarContainer: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
  },
  dailyBar: {
    height: 16,
    borderRadius: 4,
    marginRight: 10,
  },
  dailyValue: {
    fontSize: 12,
    color: "#666",
    minWidth: 50,
  },
  revenueText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#2E7D32",
    minWidth: 60,
    textAlign: "right",
  },
  insightsContainer: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 15,
  },
  insightCard: {
    backgroundColor: "#F0F8FF",
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    borderLeftWidth: 4,
    borderLeftColor: "#2196F3",
  },
  insightTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 5,
  },
  insightText: {
    fontSize: 14,
    color: "#333",
    lineHeight: 20,
  },
});