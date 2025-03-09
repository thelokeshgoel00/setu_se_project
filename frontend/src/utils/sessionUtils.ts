/**
 * Utility functions for managing session storage in the verification flow
 */

/**
 * Resets the verification flow by clearing all related session storage items
 */
export const resetVerificationFlow = () => {
  // Clear all verification-related session storage
  sessionStorage.removeItem('panVerificationResult');
  sessionStorage.removeItem('verifiedPAN');
  sessionStorage.removeItem('flowTraceId');
}; 