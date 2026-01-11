/**
 * Toast Notification Helper
 * Shows simple feedback messages to user
 */

import { Alert } from "react-native";

export interface ToastOptions {
  duration?: number; // Duration in ms (used by some toast libraries)
  position?: "top" | "bottom" | "center"; // Toast position hint
}

/**
 * Show a toast notification
 * Uses Alert for now (can be replaced with react-native-toast-message later)
 */
export function showToast(message: string, type: "success" | "error" | "info" = "info", options?: ToastOptions): void {
  // For React Native, we use Alert which is simple and built-in
  // In production, you'd use react-native-toast-message or similar
  const title = type === "success" ? "✓" : type === "error" ? "✗" : "ℹ";
  
  // Log for debugging
  console.log(`[TOAST ${type.toUpperCase()}] ${message}`);

  // Show alert (can be enhanced with toast library)
  Alert.alert(title, message, [{ text: "OK", onPress: () => {} }], {
    cancelable: true,
  });
}

/**
 * Show success toast
 */
export function showSuccessToast(message: string, options?: ToastOptions): void {
  showToast(message, "success", options);
}

/**
 * Show error toast
 */
export function showErrorToast(message: string, options?: ToastOptions): void {
  showToast(message, "error", options);
}

/**
 * Show info toast
 */
export function showInfoToast(message: string, options?: ToastOptions): void {
  showToast(message, "info", options);
}
