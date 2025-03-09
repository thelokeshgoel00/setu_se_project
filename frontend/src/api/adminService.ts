// Import the configured API instance from setuApi
import { api } from './setuApi';

export interface MetricsData {
  totalKycAttempted: number;
  totalKycSuccessful: number;
  totalKycFailed: number;
  totalKycFailedDueToPan: number;
  totalKycFailedDueToBankAccount: number;
  totalKycFailedDueToBoth: number;
}

/**
 * Fetches admin metrics from the backend API
 * @returns Promise with metrics data
 */
export const fetchAdminMetrics = async (): Promise<MetricsData> => {
  try {
    // Use the configured API instance with auth interceptor
    const response = await api.get('/admin/metrics');
    return response.data;
  } catch (error) {
    console.error('Error fetching admin metrics:', error);
    throw error;
  }
};

/**
 * Fetches PAN verification history from the backend API
 * @returns Promise with PAN verification history
 */
export const fetchPANVerificationHistory = async () => {
  try {
    // Use the configured API instance with auth interceptor
    const response = await api.get('/pan/history');
    return response.data;
  } catch (error) {
    console.error('Error fetching PAN verification history:', error);
    throw error;
  }
};

/**
 * Fetches reverse penny drop history from the backend API
 * @returns Promise with reverse penny drop history
 */
export const fetchReversePennyDropHistory = async () => {
  try {
    // Use the configured API instance with auth interceptor
    const response = await api.get('/rpd/history');
    return response.data;
  } catch (error) {
    console.error('Error fetching reverse penny drop history:', error);
    throw error;
  }
};

/**
 * Fetches payment history from the backend API
 * @returns Promise with payment history
 */
export const fetchPaymentHistory = async () => {
  try {
    // Use the configured API instance with auth interceptor
    const response = await api.get('/payments/history');
    return response.data;
  } catch (error) {
    console.error('Error fetching payment history:', error);
    throw error;
  }
}; 