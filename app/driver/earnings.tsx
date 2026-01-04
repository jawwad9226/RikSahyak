import { useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

interface EarningsData {
  today: {
    rides: number;
    earnings: number;
  };
  week: {
    rides: number;
    earnings: number;
  };
  month: {
    rides: number;
    earnings: number;
  };
  recentRides: Array<{
    id: string;
    date: string;
    pickup: string;
    dropoff: string;
    fare: number;
  }>;
}

export default function Earnings() {
  const [earnings, setEarnings] = useState<EarningsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching earnings data
    const fetchEarnings = async () => {
      try {
        // TODO: Replace with actual API call
        // const response = await fetch(`${API_BASE_URL}/api/v1/driver/earnings`);
        // const data = await response.json();

        // Dummy data for now
        const dummyEarnings: EarningsData = {
          today: {
            rides: 3,
            earnings: 195,
          },
          week: {
            rides: 18,
            earnings: 1150,
          },
          month: {
            rides: 72,
            earnings: 4500,
          },
          recentRides: [
            {
              id: "ride_001",
              date: "Today 14:30",
              pickup: "Station",
              dropoff: "Civil Lines",
              fare: 65,
            },
            {
              id: "ride_002",
              date: "Today 12:15",
              pickup: "Bus Stand",
              dropoff: "Hospital",
              fare: 45,
            },
            {
              id: "ride_003",
              date: "Today 09:45",
              pickup: "Market",
              dropoff: "Station",
              fare: 85,
            },
          ],
        };

        setEarnings(dummyEarnings);
      } catch (error) {
        console.error("Failed to fetch earnings:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEarnings();
  }, []);

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Loading earnings...</Text>
      </View>
    );
  }

  if (!earnings) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Earnings</Text>
        <Text style={styles.subtitle}>Unable to load earnings data</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Your Earnings</Text>

      <View style={styles.summaryContainer}>
        <View style={styles.summaryCard}>
          <Text style={styles.periodLabel}>Today</Text>
          <Text style={styles.ridesCount}>{earnings.today.rides} rides</Text>
          <Text style={styles.earningsAmount}>₹{earnings.today.earnings}</Text>
        </View>

        <View style={styles.summaryCard}>
          <Text style={styles.periodLabel}>This Week</Text>
          <Text style={styles.ridesCount}>{earnings.week.rides} rides</Text>
          <Text style={styles.earningsAmount}>₹{earnings.week.earnings}</Text>
        </View>

        <View style={styles.summaryCard}>
          <Text style={styles.periodLabel}>This Month</Text>
          <Text style={styles.ridesCount}>{earnings.month.rides} rides</Text>
          <Text style={styles.earningsAmount}>₹{earnings.month.earnings}</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Recent Rides</Text>

      {earnings.recentRides.map((ride) => (
        <View key={ride.id} style={styles.rideCard}>
          <View style={styles.rideHeader}>
            <Text style={styles.rideDate}>{ride.date}</Text>
            <Text style={styles.rideFare}>₹{ride.fare}</Text>
          </View>

          <View style={styles.rideRoute}>
            <Text style={styles.location}>{ride.pickup}</Text>
            <Text style={styles.arrow}>→</Text>
            <Text style={styles.location}>{ride.dropoff}</Text>
          </View>
        </View>
      ))}
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
  subtitle: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
  },
  summaryContainer: {
    marginBottom: 30,
  },
  summaryCard: {
    backgroundColor: "#F9F9F9",
    borderWidth: 2,
    borderColor: "#FFC107",
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    alignItems: "center",
  },
  periodLabel: {
    fontSize: 16,
    fontWeight: "600",
    color: "#000",
    marginBottom: 5,
  },
  ridesCount: {
    fontSize: 14,
    color: "#666",
    marginBottom: 5,
  },
  earningsAmount: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#FFC107",
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#000",
    marginBottom: 15,
  },
  rideCard: {
    backgroundColor: "#F5F5F5",
    borderRadius: 8,
    padding: 15,
    marginBottom: 10,
  },
  rideHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  rideDate: {
    fontSize: 14,
    color: "#666",
  },
  rideFare: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#4CAF50",
  },
  rideRoute: {
    flexDirection: "row",
    alignItems: "center",
  },
  location: {
    fontSize: 14,
    fontWeight: "600",
    color: "#000",
    flex: 1,
  },
  arrow: {
    fontSize: 12,
    color: "#666",
    marginHorizontal: 8,
  },
});
