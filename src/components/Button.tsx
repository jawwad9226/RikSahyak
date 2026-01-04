import { Pressable, StyleSheet, Text, TextStyle, ViewStyle } from "react-native";

interface RikButtonProps {
  onPress: () => void;
  title: string;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export default function RikButton({
  onPress,
  title,
  variant = "primary",
  disabled = false,
  style,
  textStyle,
}: RikButtonProps) {
  const getButtonStyle = () => {
    switch (variant) {
      case "primary":
        return styles.primaryButton;
      case "secondary":
        return styles.secondaryButton;
      case "danger":
        return styles.dangerButton;
      default:
        return styles.primaryButton;
    }
  };

  const getTextColor = () => {
    switch (variant) {
      case "primary":
        return { color: "#000" };
      case "secondary":
        return { color: "#FFC107" };
      case "danger":
        return { color: "#FFF" };
      default:
        return { color: "#000" };
    }
  };

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        getButtonStyle(),
        style,
        pressed && styles.pressed,
        disabled && styles.disabled,
      ]}
    >
      <Text style={[styles.text, getTextColor(), textStyle]}>{title}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  primaryButton: {
    backgroundColor: "#FFC107",
    borderWidth: 2,
    borderColor: "#000",
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 6,
    alignItems: "center",
  },
  secondaryButton: {
    backgroundColor: "#000",
    borderWidth: 2,
    borderColor: "#FFC107",
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 6,
    alignItems: "center",
  },
  dangerButton: {
    backgroundColor: "#D32F2F",
    borderWidth: 2,
    borderColor: "#000",
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 6,
    alignItems: "center",
  },
  text: {
    fontSize: 16,
    fontWeight: "bold",
  },
  pressed: {
    opacity: 0.8,
  },
  disabled: {
    opacity: 0.5,
  },
});
