/**
 * Global Error Handler and Logger
 * Centralized error management for entire app
 */

export enum ErrorType {
  NETWORK = "NETWORK_ERROR",
  TIMEOUT = "TIMEOUT_ERROR",
  NOT_FOUND = "NOT_FOUND",
  UNAUTHORIZED = "UNAUTHORIZED",
  SERVER_ERROR = "SERVER_ERROR",
  VALIDATION_ERROR = "VALIDATION_ERROR",
  UNKNOWN = "UNKNOWN_ERROR",
}

export interface AppError {
  type: ErrorType;
  message: string;
  statusCode?: number;
  originalError?: Error;
  timestamp: string;
}

/**
 * Parse error and determine error type
 */
export const parseError = (error: any, statusCode?: number): AppError => {
  const timestamp = new Date().toISOString();

  if (error instanceof TypeError) {
    if (error.message.includes("fetch")) {
      return {
        type: ErrorType.NETWORK,
        message: "Network connection failed. Check your internet connection.",
        originalError: error,
        timestamp,
      };
    }
  }

  if (statusCode === 404) {
    return {
      type: ErrorType.NOT_FOUND,
      message: "Resource not found",
      statusCode,
      originalError: error,
      timestamp,
    };
  }

  if (statusCode === 401 || statusCode === 403) {
    return {
      type: ErrorType.UNAUTHORIZED,
      message: "Unauthorized. Please log in again.",
      statusCode,
      originalError: error,
      timestamp,
    };
  }

  if (statusCode && statusCode >= 500) {
    return {
      type: ErrorType.SERVER_ERROR,
      message: "Server error. Please try again later.",
      statusCode,
      originalError: error,
      timestamp,
    };
  }

  if (statusCode === 422 || statusCode === 400) {
    return {
      type: ErrorType.VALIDATION_ERROR,
      message: "Invalid request. Please check your input.",
      statusCode,
      originalError: error,
      timestamp,
    };
  }

  return {
    type: ErrorType.UNKNOWN,
    message: error?.message || "An unknown error occurred",
    originalError: error,
    timestamp,
  };
};

/**
 * Get user-friendly error message
 */
export const getErrorMessage = (error: any): string => {
  if (error && typeof error === "object" && error.type) {
    return error.message || "An error occurred";
  }

  if (typeof error === "string") {
    return error;
  }

  if (error?.message) {
    return error.message;
  }

  return "An unexpected error occurred";
};

/**
 * Log error for debugging
 */
export const logError = (error: AppError, context?: string) => {
  const logData = {
    timestamp: error.timestamp,
    type: error.type,
    message: error.message,
    statusCode: error.statusCode,
    context,
  };

  console.error("[AppError]", logData);

  // In production, this could be sent to error tracking service
  // e.g., Sentry, LogRocket, etc.
};
