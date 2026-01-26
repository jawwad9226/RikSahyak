import { useUser } from "@/src/context/UserContext";
import { submitRideFeedback } from "@/src/services/api";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

interface RideFeedbackProps {
  rideId: string;
  driverName: string;
  onFeedbackSubmitted?: () => void;
}

export default function RideFeedback({ rideId, driverName, onFeedbackSubmitted }: RideFeedbackProps) {
  const { user } = useUser();
  const router = useRouter();
  const [rating, setRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState("");
  const [selectedIssues, setSelectedIssues] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const issues = [
    { id: "asked_more_money", label: "Asked for more money" },
    { id: "rude_behavior", label: "Rude behavior" },
    { id: "unsafe_driving", label: "Unsafe driving" },
    { id: "wrong_route", label: "Took wrong route" },
    { id: "vehicle_condition", label: "Poor vehicle condition" },
    { id: "late_pickup", label: "Late for pickup" },
  ];

  const handleIssueToggle = (issueId: string) => {
    setSelectedIssues(prev =>
      prev.includes(issueId)
        ? prev.filter(id => id !== issueId)
        : [...prev, issueId]
    );
  };

  const handleSubmitFeedback = async () => {
    if (rating === 0) {
      Alert.alert("Rating Required", "Please select a star rating for the driver.");
      return;
    }

    if (!user?.user_id) {
      Alert.alert("Error", "User not authenticated");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await submitRideFeedback(
        rideId,
        user.user_id,
        rating,
        feedbackText,
        selectedIssues
      );

      if (response.success) {
        Alert.alert(
          "Thank You!",
          "Your feedback helps improve our service.",
          [
            {
              text: "OK",
              onPress: () => {
                onFeedbackSubmitted?.();
                router.back();
              }
            }
          ]
        );
      } else {
        Alert.alert("Error", response.error || "Failed to submit feedback");
      }
    } catch (error) {
      Alert.alert("Error", "Failed to submit feedback: " + String(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStars = () => {
    return (
      <View style={styles.starsContainer}>
        {[1, 2, 3, 4, 5].map((star) => (
          <Pressable
            key={star}
            onPress={() => setRating(star)}
            style={styles.starButton}
          >
            <Text style={[styles.star, rating >= star && styles.starSelected]}>
              ★
            </Text>
          </Pressable>
        ))}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Rate Your Ride</Text>
      <Text style={styles.subtitle}>How was your experience with {driverName}?</Text>

      <View style={styles.ratingSection}>
        <Text style={styles.ratingLabel}>Overall Rating</Text>
        {renderStars()}
        <Text style={styles.ratingText}>
          {rating === 0 ? "Tap stars to rate" :
           rating === 1 ? "Poor" :
           rating === 2 ? "Fair" :
           rating === 3 ? "Good" :
           rating === 4 ? "Very Good" : "Excellent"}
        </Text>
      </View>

      <View style={styles.issuesSection}>
        <Text style={styles.issuesLabel}>Any issues? (Optional)</Text>
        <View style={styles.issuesContainer}>
          {issues.map((issue) => (
            <Pressable
              key={issue.id}
              style={[
                styles.issueButton,
                selectedIssues.includes(issue.id) && styles.issueButtonSelected
              ]}
              onPress={() => handleIssueToggle(issue.id)}
            >
              <Text style={[
                styles.issueText,
                selectedIssues.includes(issue.id) && styles.issueTextSelected
              ]}>
                {issue.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      <View style={styles.feedbackSection}>
        <Text style={styles.feedbackLabel}>Additional Comments (Optional)</Text>
        <TextInput
          style={styles.feedbackInput}
          placeholder="Tell us more about your experience..."
          value={feedbackText}
          onChangeText={setFeedbackText}
          multiline
          numberOfLines={3}
          maxLength={500}
        />
      </View>

      <Pressable
        style={[styles.submitButton, isSubmitting && styles.submitButtonDisabled]}
        onPress={handleSubmitFeedback}
        disabled={isSubmitting}
      >
        <Text style={styles.submitButtonText}>
          {isSubmitting ? "Submitting..." : "Submit Feedback"}
        </Text>
      </Pressable>
    </View>
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
    textAlign: "center",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
    marginBottom: 30,
  },
  ratingSection: {
    alignItems: "center",
    marginBottom: 30,
  },
  ratingLabel: {
    fontSize: 18,
    fontWeight: "600",
    color: "#000",
    marginBottom: 15,
  },
  starsContainer: {
    flexDirection: "row",
    marginBottom: 10,
  },
  starButton: {
    padding: 5,
  },
  star: {
    fontSize: 40,
    color: "#DDD",
  },
  starSelected: {
    color: "#FFD700",
  },
  ratingText: {
    fontSize: 16,
    color: "#666",
    fontWeight: "500",
  },
  issuesSection: {
    marginBottom: 30,
  },
  issuesLabel: {
    fontSize: 18,
    fontWeight: "600",
    color: "#000",
    marginBottom: 15,
  },
  issuesContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  issueButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#DDD",
    backgroundColor: "#F9F9F9",
  },
  issueButtonSelected: {
    backgroundColor: "#FF4444",
    borderColor: "#FF4444",
  },
  issueText: {
    fontSize: 14,
    color: "#666",
  },
  issueTextSelected: {
    color: "#FFF",
    fontWeight: "500",
  },
  feedbackSection: {
    marginBottom: 30,
  },
  feedbackLabel: {
    fontSize: 18,
    fontWeight: "600",
    color: "#000",
    marginBottom: 10,
  },
  feedbackInput: {
    borderWidth: 1,
    borderColor: "#DDD",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    minHeight: 80,
    textAlignVertical: "top",
  },
  submitButton: {
    backgroundColor: "#4CAF50",
    paddingVertical: 15,
    borderRadius: 8,
    alignItems: "center",
  },
  submitButtonDisabled: {
    backgroundColor: "#CCC",
  },
  submitButtonText: {
    color: "#FFF",
    fontSize: 18,
    fontWeight: "600",
  },
});