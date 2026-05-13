/**
 * Robust API Client with Error Handling and Retry Logic
 * Handles all HTTP requests across the app
 */

import { API_CONFIG, getEndpointUrl } from "@/src/config/env";
import { getErrorMessage, logError, parseError } from "@/src/utils/errorHandler";

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  statusCode?: number;
}

/**
 * Retry logic with exponential backoff
 */
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Make HTTP request with retry logic
 */
async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retryCount = 0
): Promise<Response> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.REQUEST_TIMEOUT);

    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response;
  } catch (error: any) {
    clearTimeout(undefined);

    // Retry on network errors
    if (retryCount < API_CONFIG.MAX_RETRIES) {
      const backoffDelay = API_CONFIG.RETRY_DELAY * Math.pow(2, retryCount);
      console.warn(
        `Request failed (attempt ${retryCount + 1}/${API_CONFIG.MAX_RETRIES}), retrying in ${backoffDelay}ms...`,
        url
      );
      await delay(backoffDelay);
      return fetchWithRetry(url, options, retryCount + 1);
    }

    throw error;
  }
}

/**
 * Safe JSON parse
 */
const safeJsonParse = async (response: Response) => {
  try {
    return await response.json();
  } catch (error) {
    console.warn("Failed to parse JSON response", response.status);
    return {};
  }
};

/**
 * Make a GET request
 */
export async function apiGet<T = any>(endpoint: string): Promise<ApiResponse<T>> {
  try {
    const url = getEndpointUrl(endpoint);
    console.log(`[GET] ${url}`);

    const response = await fetchWithRetry(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "x-admin-token": API_CONFIG.ADMIN_SECRET_KEY,
      },
    });

    const data = await safeJsonParse(response);

    if (!response.ok) {
      const error = parseError(data, response.status);
      logError(error, `GET ${endpoint}`);
      return {
        success: false,
        error: getErrorMessage(error),
        statusCode: response.status,
      };
    }

    return { success: true, data, statusCode: response.status };
  } catch (error: any) {
    const appError = parseError(error);
    logError(appError, `GET ${endpoint}`);
    return { success: false, error: getErrorMessage(appError) };
  }
}

/**
 * Make a POST request
 */
export async function apiPost<T = any>(
  endpoint: string,
  body?: any
): Promise<ApiResponse<T>> {
  try {
    const url = getEndpointUrl(endpoint);
    console.log(`[POST] ${url}`, body);

    const response = await fetchWithRetry(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-admin-token": API_CONFIG.ADMIN_SECRET_KEY,
      },
      body: JSON.stringify(body || {}),
    });

    const data = await safeJsonParse(response);

    if (!response.ok) {
      const error = parseError(data, response.status);
      logError(error, `POST ${endpoint}`);
      return {
        success: false,
        error: getErrorMessage(error),
        statusCode: response.status,
      };
    }

    return { success: true, data, statusCode: response.status };
  } catch (error: any) {
    const appError = parseError(error);
    logError(appError, `POST ${endpoint}`);
    return { success: false, error: getErrorMessage(appError) };
  }
}

/**
 * Make a PUT request
 */
export async function apiPut<T = any>(
  endpoint: string,
  body?: any
): Promise<ApiResponse<T>> {
  try {
    const url = getEndpointUrl(endpoint);
    console.log(`[PUT] ${url}`, body);

    const response = await fetchWithRetry(url, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "x-admin-token": API_CONFIG.ADMIN_SECRET_KEY,
      },
      body: JSON.stringify(body || {}),
    });

    const data = await safeJsonParse(response);

    if (!response.ok) {
      const error = parseError(data, response.status);
      logError(error, `PUT ${endpoint}`);
      return {
        success: false,
        error: getErrorMessage(error),
        statusCode: response.status,
      };
    }

    return { success: true, data, statusCode: response.status };
  } catch (error: any) {
    const appError = parseError(error);
    logError(appError, `PUT ${endpoint}`);
    return { success: false, error: getErrorMessage(appError) };
  }
}

/**
 * Make a DELETE request
 */
export async function apiDelete<T = any>(endpoint: string): Promise<ApiResponse<T>> {
  try {
    const url = getEndpointUrl(endpoint);
    console.log(`[DELETE] ${url}`);

    const response = await fetchWithRetry(url, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "x-admin-token": API_CONFIG.ADMIN_SECRET_KEY,
      },
    });

    const data = await safeJsonParse(response);

    if (!response.ok) {
      const error = parseError(data, response.status);
      logError(error, `DELETE ${endpoint}`);
      return {
        success: false,
        error: getErrorMessage(error),
        statusCode: response.status,
      };
    }

    return { success: true, data, statusCode: response.status };
  } catch (error: any) {
    const appError = parseError(error);
    logError(appError, `DELETE ${endpoint}`);
    return { success: false, error: getErrorMessage(appError) };
  }
}

export default {
  apiGet,
  apiPost,
  apiPut,
  apiDelete,
};
