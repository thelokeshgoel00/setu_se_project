import axios from 'axios';

// Define types for authentication
export interface UserRegister {
  username: string;
  email: string;
  password: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

// Define enum to match backend
export enum UserRole {
  ADMIN = "ADMIN",
  MEMBER = "MEMBER"
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

// Create axios instance with the correct base URL
const authApi = axios.create({
  baseURL: 'http://localhost:8000/api/auth',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include token in requests
authApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Authentication functions
export const registerUser = async (userData: UserRegister): Promise<User> => {
  const response = await authApi.post('/register', userData);
  return response.data;
};

export const loginUser = async (credentials: UserLogin): Promise<AuthToken> => {
  // For login, we need to use form data format as required by OAuth2
  const formData = new FormData();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);
  
  const response = await axios.post('http://localhost:8000/api/auth/token', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  
  // Store token in localStorage
  const token = response.data;
  localStorage.setItem('token', token.access_token);
  
  return token;
};

export const getCurrentUser = async (): Promise<User | null> => {
  try {
    const response = await authApi.get('/me');
    return response.data;
  } catch (error) {
    return null;
  }
};

export const logout = (): void => {
  localStorage.removeItem('token');
};

// Helper function to check if user is authenticated
export const isAuthenticated = (): boolean => {
  return localStorage.getItem('token') !== null;
};

// Helper function to check if user is admin
export const isAdmin = async (): Promise<boolean> => {
  const user = await getCurrentUser();
  return user?.role === UserRole.ADMIN;
};

// Update the main API instance to include authentication
export const setupAuthInterceptor = (apiInstance: any): void => {
  apiInstance.interceptors.request.use(
    (config: any) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error: any) => {
      return Promise.reject(error);
    }
  );
}; 