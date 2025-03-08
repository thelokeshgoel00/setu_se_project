import axios from 'axios';

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
    const response = await axios.get('/api/admin/metrics');
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
    const response = await axios.get('/api/pan/history');
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
    const response = await axios.get('/api/rpd/history');
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
    const response = await axios.get('/api/payments/history');
    return response.data;
  } catch (error) {
    console.error('Error fetching payment history:', error);
    throw error;
  }
}; 