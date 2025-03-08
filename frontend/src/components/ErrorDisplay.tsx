import React, { useEffect, useState } from 'react';

interface ErrorDisplayProps {
  error: string | null;
  title?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  showIcon?: boolean;
  variant?: 'standard' | 'detailed';
  errorCode?: string;
  suggestion?: string;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  title = 'Error Occurred',
  onRetry,
  onDismiss,
  showIcon = true,
  variant = 'standard',
  errorCode,
  suggestion,
}) => {
  const [animate, setAnimate] = useState(false);
  
  useEffect(() => {
    if (error) {
      setAnimate(true);
      const timer = setTimeout(() => setAnimate(false), 500);
      return () => clearTimeout(timer);
    }
  }, [error]);

  if (!error) return null;

  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-5 mb-6 animate-fadeIn ${animate ? 'animate-shake' : ''}`}>
      <div className="flex items-start">
        {showIcon && (
          <div className="mr-4 flex-shrink-0">
            <svg className="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        )}
        
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-red-800 mb-2">{title}</h3>
          
          <div className="text-red-700 mb-4">
            {variant === 'detailed' ? (
              <div className="space-y-2">
                <p className="font-medium">{error}</p>
                {errorCode && (
                  <div className="bg-red-100 p-2 rounded text-sm">
                    <span className="font-mono">Error Code: {errorCode}</span>
                  </div>
                )}
                {suggestion && (
                  <p className="text-sm italic">{suggestion}</p>
                )}
              </div>
            ) : (
              <div>
                <p>{error}</p>
                {suggestion && (
                  <p className="text-sm italic mt-2">{suggestion}</p>
                )}
              </div>
            )}
          </div>
          
          <div className="flex space-x-3">
            {onRetry && (
              <button 
                onClick={onRetry}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
              >
                Try Again
              </button>
            )}
            
            {onDismiss && (
              <button 
                onClick={onDismiss}
                className="px-4 py-2 bg-white border border-red-300 text-red-700 rounded-md hover:bg-red-50 transition-colors text-sm font-medium"
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