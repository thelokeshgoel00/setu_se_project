import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { verifyPAN, PANVerificationRequest, PANVerificationResponse } from '../api/setuApi'
import ErrorDisplay from '../components/ErrorDisplay'
import { parseApiError, extractSetuErrorCode, getSetuErrorMessage } from '../utils/errorUtils'

const PANVerification = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState<PANVerificationRequest>({
    pan: '',
    consent: 'N',
    reason: ''
  })
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<{
    message: string;
    code?: string;
    title?: string;
    suggestion?: string;
  } | null>(null)
  const [result, setResult] = useState<PANVerificationResponse | null>(null)
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    
    try {
      // Validate PAN format
      const panRegex = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/
      if (!panRegex.test(formData.pan)) {
        throw new Error('Invalid PAN format. Expected format: ABCDE1234A')
      }
      
      // Validate reason length
      if (formData.reason.length < 20) {
        throw new Error('Reason must be at least 20 characters long')
      }
      
      const response = await verifyPAN(formData)
      setResult(response)
      
      // Store PAN verification result in session storage for the next step
      sessionStorage.setItem('panVerificationResult', JSON.stringify(response))
      sessionStorage.setItem('verifiedPAN', formData.pan)
    } catch (err: any) {
      // Use our error parsing utility
      const parsedError = parseApiError(err);
      
      // Check for Setu-specific error codes
      const setuErrorCode = extractSetuErrorCode(err);
      if (setuErrorCode) {
        parsedError.message = getSetuErrorMessage(setuErrorCode);
        parsedError.code = setuErrorCode;
      }
      
      setError(parsedError);
    } finally {
      setLoading(false)
    }
  }
  
  const handleContinue = () => {
    navigate('/reverse-penny-drop')
  }
  
  const handleRetry = () => {
    setError(null);
    // Focus on the PAN input field
    const panInput = document.getElementById('pan');
    if (panInput) {
      panInput.focus();
    }
  }
  
  const handleDismissError = () => {
    setError(null);
  }
  
  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Verification Process</h1>
      <div className="flex items-center mb-8">
        <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-2">1</div>
        <span className="font-medium">PAN Verification</span>
        <div className="mx-4 border-t border-gray-300 flex-grow"></div>
        <div className="bg-gray-300 text-gray-600 rounded-full w-8 h-8 flex items-center justify-center mr-2">2</div>
        <span className="text-gray-500">Bank Account Verification</span>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-xl font-semibold mb-4">Verify a PAN Number</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="pan" className="block text-gray-700 font-medium mb-2">
              PAN Number
            </label>
            <input
              type="text"
              id="pan"
              name="pan"
              value={formData.pan}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-input-border rounded-md focus:outline-none focus:ring-2 focus:ring-input-focus bg-input-background text-input-text"
              placeholder="ABCDE1234A"
              required
            />
            <p className="text-sm text-gray-500 mt-1">Format: 5 uppercase letters, 4 digits, 1 uppercase letter</p>
          </div>
          
          <div className="mb-4">
            <label htmlFor="reason" className="block text-gray-700 font-medium mb-2">
              Reason for Verification
            </label>
            <textarea
              id="reason"
              name="reason"
              value={formData.reason}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-input-border rounded-md focus:outline-none focus:ring-2 focus:ring-input-focus bg-input-background text-input-text"
              placeholder="Enter reason for verification (min 20 characters)"
              rows={3}
              required
            />
            <p className="text-sm text-gray-500 mt-1">Minimum 20 characters required</p>
          </div>
          
          <div className="mb-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.consent === 'Y'}
                onChange={() => setFormData(prev => ({ ...prev, consent: prev.consent === 'Y' ? 'N' : 'Y' }))}
                className="mr-2 bg-input-background text-input-text"
                required
              />
              <span className="text-gray-700">I consent to verify this PAN number</span>
            </label>
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition disabled:bg-blue-300"
          >
            {loading ? 'Verifying...' : 'Verify PAN'}
          </button>
        </form>
      </div>
      
      {error && (
        <ErrorDisplay 
          error={error.message}
          title={error.title || 'PAN Verification Failed'}
          errorCode={error.code}
          variant="detailed"
          onRetry={handleRetry}
          onDismiss={handleDismissError}
        />
      )}
      
      {result && (
        <div className="bg-green-50 border border-green-200 p-6 rounded-lg">
          <h3 className="text-xl font-semibold mb-4 text-green-800">Verification Result</h3>
          
          <div className="bg-white p-4 rounded-md border border-green-100 mb-4">
            <h4 className="font-medium text-gray-700 mb-2">PAN Details</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Full Name</p>
                <p className="font-medium text-input-text">{result.data.full_name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Category</p>
                <p className="font-medium text-input-text">{result.data.category}</p>
              </div>
              {result.data.aadhaar_seeding_status && (
                <div>
                  <p className="text-sm text-gray-500">Aadhaar Seeding Status</p>
                  <p className="font-medium text-input-text">{result.data.aadhaar_seeding_status}</p>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex justify-between text-sm text-gray-500 mb-6">
            <p>Status: <span className="text-input-text">{result.status}</span></p>
            <p>Trace ID: <span className="text-input-text">{result.trace_id}</span></p>
          </div>
          
          <button
            onClick={handleContinue}
            className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 transition"
          >
            Continue to Bank Account Verification
          </button>
        </div>
      )}
    </div>
  )
}

export default PANVerification 