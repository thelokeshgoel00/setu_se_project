import { useNavigate } from 'react-router-dom';
import { resetVerificationFlow } from '../utils/sessionUtils';

interface ErrorDisplayProps {
  error: {
    message: string;
    code?: string;
    title?: string;
    suggestion?: string;
  };
  onRetry?: () => void;
  onDismiss?: () => void;
}

const ErrorDisplay = ({ error, onRetry, onDismiss }: ErrorDisplayProps) => {
  const navigate = useNavigate();
  
  // Check if this is a trace_id error or a verification flow error
  const isTraceIdError = error.message && (
    error.message.toLowerCase().includes('trace_id') || 
    error.message.toLowerCase().includes('verification flow') ||
    (error.code && error.code.toLowerCase() === 'failed')
  );
  
  const handleRestartVerification = () => {
    // Reset the verification flow
    resetVerificationFlow();
    
    // Navigate to the PAN verification page
    navigate('/pan-verification');
  };
  
  return (
    <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-800">
            {error.title || 'Error'}
            {error.code && <span className="text-xs ml-2 text-red-600">({error.code})</span>}
          </h3>
          <div className="mt-2 text-sm text-red-700">
            <p>{error.message}</p>
            {error.suggestion && (
              <p className="mt-1 text-red-600">{error.suggestion}</p>
            )}
          </div>
          <div className="mt-4">
            {isTraceIdError ? (
              <button
                type="button"
                onClick={handleRestartVerification}
                className="mr-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Restart Verification
              </button>
            ) : (
              onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className="mr-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  Try Again
                </button>
              )
            )}
            {onDismiss && (
              <button
                type="button"
                onClick={onDismiss}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorDisplay; 