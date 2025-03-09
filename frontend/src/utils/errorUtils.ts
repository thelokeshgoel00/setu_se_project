interface ParsedError {
  message: string;
  code?: string;
  title?: string;
  suggestion?: string;
}

/**
 * Parses API errors and provides user-friendly messages
 */
export const parseApiError = (error: any): ParsedError => {
  // Default error message
  let result: ParsedError = {
    message: 'An unexpected error occurred. Please try again.',
  };

  // Handle axios error responses
  if (error.response) {
    const { status, data } = error.response;
    
    // Check if the response has the new error format (status, message, trace_id)
    if (data && typeof data === 'object' && 'status' in data && 'message' in data) {
      return {
        message: data.message,
        code: data.status.toUpperCase(),
        title: getErrorTitle(data.status),
        suggestion: getSuggestionForStatus(data.status),
      };
    }
    
    // Extract error message from response data
    const errorMessage = data?.detail || data?.message || data?.error || JSON.stringify(data);
    
    // Handle different status codes
    switch (status) {
      case 400:
        result = {
          message: errorMessage,
          code: 'BAD_REQUEST',
          title: 'Invalid Request',
          suggestion: 'Please check your input and try again.',
        };
        break;
      case 401:
        result = {
          message: 'You are not authorized to perform this action.',
          code: 'UNAUTHORIZED',
          title: 'Authentication Error',
          suggestion: 'Please log in again and retry.',
        };
        break;
      case 403:
        result = {
          message: 'You do not have permission to perform this action.',
          code: 'FORBIDDEN',
          title: 'Permission Denied',
          suggestion: 'Please contact support if you believe this is an error.',
        };
        break;
      case 404:
        result = {
          message: 'The requested resource was not found.',
          code: 'NOT_FOUND',
          title: 'Resource Not Found',
          suggestion: 'Please check the URL or parameters and try again.',
        };
        break;
      case 409:
        result = {
          message: errorMessage,
          code: 'CONFLICT',
          title: 'Request Conflict',
          suggestion: 'The request conflicts with the current state of the resource.',
        };
        break;
      case 422:
        result = {
          message: errorMessage,
          code: 'VALIDATION_ERROR',
          title: 'Validation Error',
          suggestion: 'Please check your input and try again.',
        };
        break;
      case 429:
        result = {
          message: 'Too many requests. Please try again later.',
          code: 'RATE_LIMITED',
          title: 'Rate Limited',
          suggestion: 'Please wait a moment before trying again.',
        };
        break;
      case 500:
      case 502:
      case 503:
      case 504:
        result = {
          message: 'The server encountered an error. Please try again later.',
          code: 'SERVER_ERROR',
          title: 'Server Error',
          suggestion: 'This is not your fault. Please try again later or contact support.',
        };
        break;
      default:
        result = {
          message: errorMessage,
          code: `HTTP_${status}`,
          title: 'Error',
        };
    }
  } 
  // Handle network errors
  else if (error.request) {
    result = {
      message: 'Unable to connect to the server. Please check your internet connection.',
      code: 'NETWORK_ERROR',
      title: 'Connection Error',
      suggestion: 'Please check your internet connection and try again.',
    };
  } 
  // Handle validation errors from our app
  else if (error.message && error.message.includes('Invalid')) {
    result = {
      message: error.message,
      code: 'VALIDATION_ERROR',
      title: 'Validation Error',
      suggestion: 'Please check your input and try again.',
    };
  }
  // Handle other errors with message property
  else if (error.message) {
    result = {
      message: error.message,
      code: 'APP_ERROR',
      title: 'Application Error',
    };
  }

  return result;
};

/**
 * Extracts error code from Setu API responses
 */
export const extractSetuErrorCode = (error: any): string | undefined => {
  if (error?.response?.data?.error_code) {
    return error.response.data.error_code;
  }
  
  if (error?.response?.data?.detail?.includes('code')) {
    try {
      const match = error.response.data.detail.match(/code:\s*([A-Z_]+)/i);
      if (match && match[1]) {
        return match[1];
      }
    } catch (e) {
      // Ignore parsing errors
    }
  }
  
  return undefined;
};

/**
 * Gets a user-friendly message for common Setu API error codes
 */
export const getSetuErrorMessage = (errorCode: string): string => {
  const errorMessages: Record<string, string> = {
    'INVALID_PAN': 'The PAN number provided is invalid. Please check and try again.',
    'PAN_NOT_FOUND': 'The PAN number could not be found in the database.',
    'INVALID_ACCOUNT': 'The bank account details provided are invalid.',
    'ACCOUNT_NOT_FOUND': 'The bank account could not be found.',
    'INVALID_IFSC': 'The IFSC code provided is invalid. Please check and try again.',
    'PAYMENT_EXPIRED': 'The payment request has expired. Please create a new request.',
    'PAYMENT_FAILED': 'The payment transaction failed. Please try again.',
    'INSUFFICIENT_FUNDS': 'The transaction failed due to insufficient funds.',
    'INVALID_REQUEST': 'The request format is invalid. Please check your inputs.',
    'SERVICE_UNAVAILABLE': 'The service is currently unavailable. Please try again later.',
  };
  
  return errorMessages[errorCode] || 'An error occurred with the verification service.';
};

/**
 * Get a user-friendly title based on the error status
 */
const getErrorTitle = (status: string): string => {
  const statusMap: Record<string, string> = {
    'failed': 'Verification Failed',
    'error': 'System Error',
    'not_found': 'Resource Not Found',
    'connection_error': 'Connection Error',
    'invalid_request': 'Invalid Request',
  };
  
  return statusMap[status.toLowerCase()] || 'Error';
};

/**
 * Get a suggestion based on the error status
 */
const getSuggestionForStatus = (status: string): string => {
  const suggestionMap: Record<string, string> = {
    'failed': 'Please check your information and try again.',
    'error': 'This is not your fault. Please try again later or contact support.',
    'not_found': 'Please check the information you provided and try again.',
    'connection_error': 'Please check your internet connection and try again.',
    'invalid_request': 'Please check your input and try again.',
  };
  
  return suggestionMap[status.toLowerCase()] || 'Please try again or contact support.';
}; 