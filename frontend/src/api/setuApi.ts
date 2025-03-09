import axios from 'axios';
import { setupAuthInterceptor } from './authService';

// Define types for API requests and responses
export interface PANVerificationRequest {
  pan: string;
  consent: string;
  reason: string;
}

export interface PANData {
  aadhaar_seeding_status?: string;
  category: string;
  full_name: string;
  first_name?: string;
  middle_name?: string;
  last_name?: string;
}

export interface PANVerificationResponse {
  status: string;
  data: PANData;
  message: string;
  trace_id: string;
}

export interface PANVerificationErrorResponse {
  status: string;
  message: string;
  trace_id: string;
}

export interface RedirectionConfig {
  redirectUrl: string;
  timeout: number;
}

export interface ReversePennyDropRequest {
  additionalData?: Record<string, string>;
  redirectionConfig?: RedirectionConfig;
}

export interface ReversePennyDropResponse {
  id: string;
  short_url: string;
  status: string;
  trace_id: string;
  upi_bill_id: string;
  upi_link: string;
  valid_upto: string;
}

export interface ReversePennyDropErrorResponse {
  status: string;
  message: string;
  trace_id: string;
}

// Create axios instance with the correct base URL
// In Docker, we need to use the absolute URL to the backend
export const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Setup authentication interceptor
setupAuthInterceptor(api);

// Add request interceptor to handle errors
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    return Promise.reject(error);
  }
);

// API functions
export const verifyPAN = async (data: PANVerificationRequest): Promise<PANVerificationResponse> => {
  const response = await api.post('/pan/verify', data);
  return response.data;
};

export const createReversePennyDrop = async (data: ReversePennyDropRequest): Promise<ReversePennyDropResponse> => {
  const response = await api.post('/rpd/create_request', data);
  return response.data;
};

export const mockPayment = async (requestId: string, paymentStatus: boolean): Promise<{ success: boolean; trace_id: string }> => {
  const response = await api.post(`/rpd/mock-payment`, { request_id: requestId, payment_status: paymentStatus });
  return response.data;
}; 