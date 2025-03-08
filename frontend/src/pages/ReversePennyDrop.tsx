import { useState, FormEvent, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { createReversePennyDrop, mockPayment, ReversePennyDropRequest, ReversePennyDropResponse } from '../api/setuApi'
import ErrorDisplay from '../components/ErrorDisplay'
import { parseApiError, extractSetuErrorCode, getSetuErrorMessage } from '../utils/errorUtils'

const ReversePennyDrop = () => {
  const navigate = useNavigate()
  const [panVerified, setPanVerified] = useState(false)
  const [panDetails, setPanDetails] = useState<any>(null)
  const [verifiedPan, setVerifiedPan] = useState('')
  
  const [formData, setFormData] = useState<{
    accountNumber: string;
    ifsc: string;
    accountHolderName: string;
    customerId: string;
    redirectUrl: string;
    timeout: number;
  }>({
    accountNumber: '',
    ifsc: '',
    accountHolderName: '',
    customerId: '',
    redirectUrl: 'https://example.com/callback',
    timeout: 30
  })
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<{
    message: string;
    code?: string;
    title?: string;
    suggestion?: string;
  } | null>(null)
  const [result, setResult] = useState<ReversePennyDropResponse | null>(null)
  const [mockStatus, setMockStatus] = useState<{ success: boolean; message: string } | null>(null)
  
  // Check if PAN is verified on component mount
  useEffect(() => {
    const panResult = sessionStorage.getItem('panVerificationResult')
    const pan = sessionStorage.getItem('verifiedPAN')
    
    if (panResult && pan) {
      try {
        const parsedResult = JSON.parse(panResult)
        setPanDetails(parsedResult)
        setVerifiedPan(pan)
        setPanVerified(true)
        
        // Pre-fill account holder name if available
        if (parsedResult.data && parsedResult.data.full_name) {
          setFormData(prev => ({
            ...prev,
            accountHolderName: parsedResult.data.full_name,
            customerId: `PAN_${pan}`
          }))
        }
      } catch (err) {
        console.error('Error parsing PAN verification result', err)
      }
    } else {
      // Redirect to PAN verification if not verified
      navigate('/pan-verification')
    }
  }, [navigate])
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    setMockStatus(null)
    
    try {
      // Validate account number and IFSC
      if (!/^\d{9,18}$/.test(formData.accountNumber)) {
        throw new Error('Invalid account number. It should be 9-18 digits')
      }
      
      if (!/^[A-Z]{4}0[A-Z0-9]{6}$/.test(formData.ifsc)) {
        throw new Error('Invalid IFSC code. Format should be like SBIN0000001')
      }
      
      const request: ReversePennyDropRequest = {
        additionalData: {
          customerId: formData.customerId,
          accountNumber: formData.accountNumber,
          ifsc: formData.ifsc,
          accountHolderName: formData.accountHolderName,
          verifiedPan: verifiedPan
        },
        redirectionConfig: {
          redirectUrl: formData.redirectUrl,
          timeout: formData.timeout
        }
      }
      
      const response = await createReversePennyDrop(request)
      setResult(response)
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
  
  const handleMockPayment = async (status: boolean) => {
    if (!result) return
    
    setMockStatus(null)
    setLoading(true)
    
    try {
      const response = await mockPayment(result.id, status)
      setMockStatus({
        success: response.success,
        message: `Mock payment ${status} successfully simulated`
      })
    } catch (err: any) {
      // Use our error parsing utility for mock payment errors too
      const parsedError = parseApiError(err);
      setMockStatus({
        success: false,
        message: parsedError.message
      });
    } finally {
      setLoading(false)
    }
  }
  
  const handleRetry = () => {
    setError(null);
    // Focus on the account number input field
    const accountInput = document.getElementById('accountNumber');
    if (accountInput) {
      accountInput.focus();
    }
  }
  
  const handleDismissError = () => {
    setError(null);
  }
  
  if (!panVerified) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-lg">
          <h3 className="text-xl font-semibold mb-4 text-yellow-800">PAN Verification Required</h3>
          <p className="mb-4">You need to verify your PAN before proceeding to bank account verification.</p>
          <button
            onClick={() => navigate('/pan-verification')}
            className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition"
          >
            Go to PAN Verification
          </button>
        </div>
      </div>
    )
  }
  
  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Verification Process</h1>
      <div className="flex items-center mb-8">
        <div className="bg-green-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-2">✓</div>
        <span className="font-medium text-green-600">PAN Verification</span>
        <div className="mx-4 border-t border-gray-300 flex-grow"></div>
        <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center mr-2">2</div>
        <span className="font-medium">Bank Account Verification</span>
      </div>
      
      {panDetails && (
        <div className="bg-green-50 border border-green-200 p-4 rounded-lg mb-6">
          <h3 className="font-medium text-green-800 mb-2">Verified PAN: {verifiedPan}</h3>
          <p className="text-sm text-gray-600">Name: {panDetails.data.full_name}</p>
        </div>
      )}
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-xl font-semibold mb-4">Bank Account Verification</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="accountNumber" className="block text-gray-700 font-medium mb-2">
              Account Number
            </label>
            <input
              type="text"
              id="accountNumber"
              name="accountNumber"
              value={formData.accountNumber}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-input-border rounded-md focus:outline-none focus:ring-2 focus:ring-input-focus bg-input-background text-input-text"
              placeholder="Enter bank account number"
              required
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="ifsc" className="block text-gray-700 font-medium mb-2">
              IFSC Code
            </label>
            <input
              type="text"
              id="ifsc"
              name="ifsc"
              value={formData.ifsc}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-input-border rounded-md focus:outline-none focus:ring-2 focus:ring-input-focus bg-input-background text-input-text"
              placeholder="SBIN0000001"
              required
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="accountHolderName" className="block text-gray-700 font-medium mb-2">
              Account Holder Name
            </label>
            <input
              type="text"
              id="accountHolderName"
              name="accountHolderName"
              value={formData.accountHolderName}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-input-border rounded-md focus:outline-none focus:ring-2 focus:ring-input-focus bg-input-background text-input-text"
              placeholder="Enter account holder name"
              required
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="redirectUrl" className="block text-gray-700 font-medium mb-2">
              Redirect URL
            </label>
            <input
              type="url"
              id="redirectUrl"
              name="redirectUrl"
              value={formData.redirectUrl}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-input-border rounded-md focus:outline-none focus:ring-2 focus:ring-input-focus bg-input-background text-input-text"
              placeholder="https://example.com/callback"
              required
            />
          </div>
          
          <div className="mb-6">
            <label htmlFor="timeout" className="block text-gray-700 font-medium mb-2">
              Timeout (seconds)
            </label>
            <input
              type="number"
              id="timeout"
              name="timeout"
              value={formData.timeout}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-input-border rounded-md focus:outline-none focus:ring-2 focus:ring-input-focus bg-input-background text-input-text"
              min="5"
              max="300"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition disabled:bg-blue-300"
          >
            {loading ? 'Creating...' : 'Verify Bank Account'}
          </button>
        </form>
      </div>
      
      {error && (
        <ErrorDisplay 
          error={error.message}
          title={error.title || 'Bank Account Verification Failed'}
          errorCode={error.code}
          variant="detailed"
          onRetry={handleRetry}
          onDismiss={handleDismissError}
          suggestion={error.suggestion}
        />
      )}
      
      {result && (
        <div className="bg-green-50 border border-green-200 p-6 rounded-lg mb-8">
          <h3 className="text-xl font-semibold mb-4 text-green-800">Bank Verification Request Created</h3>
          
          <div className="bg-white p-4 rounded-md border border-green-100 mb-4">
            <h4 className="font-medium text-gray-700 mb-2">Payment Details</h4>
            <p className="text-sm text-gray-600 mb-4">
              To verify your bank account, please make a payment of ₹1 using the UPI link or QR code below.
            </p>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <p className="text-sm text-gray-500">Request ID</p>
                <p className="font-medium text-input-text">{result.id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Status</p>
                <p className="font-medium text-input-text">{result.status}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">UPI Link</p>
                <p className="font-medium break-all text-blue-500"><a href={result.upi_link} target="_blank" rel="noopener noreferrer">{result.upi_link}</a></p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Short URL</p>
                <a 
                  href={result.short_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="font-medium text-blue-600 hover:underline break-all"
                >
                  {result.short_url}
                </a>
              </div>
              <div>
                <p className="text-sm text-gray-500">Valid Until</p>
                <p className="font-medium text-input-text">{new Date(result.valid_upto).toLocaleString()}</p>
              </div>
            </div>
          </div>
          
          <div className="flex justify-between text-sm text-gray-500">
            <p>UPI Bill ID: <span className="text-input-text">{result.upi_bill_id}</span></p>
            <p>Trace ID: <span className="text-input-text">{result.trace_id}</span></p>
          </div>
          
          <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <h4 className="font-medium text-yellow-800 mb-2">Sandbox Testing</h4>
            <p className="text-sm text-gray-600 mb-4">
              In sandbox mode, you can simulate a payment response without making an actual payment.
            </p>
            <div className="flex space-x-4">
              <button
                onClick={() => handleMockPayment(true)}
                disabled={loading}
                className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition disabled:bg-green-300"
              >
                Simulate Successful Payment
              </button>
              <button
                onClick={() => handleMockPayment(false)}
                disabled={loading}
                className="bg-yellow-600 text-white py-2 px-4 rounded-md hover:bg-yellow-700 transition disabled:bg-yellow-300"
              >
                Simulate Expired Payment
              </button>
            </div>
          </div>
        </div>
      )}
      
      {mockStatus && (
        <div className={`p-5 rounded-lg mb-8 ${mockStatus.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-start">
            <div className="mr-4 flex-shrink-0">
              {mockStatus.success ? (
                <svg className="h-6 w-6 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </div>
            <div>
              <h3 className={`font-semibold mb-2 ${mockStatus.success ? 'text-green-800' : 'text-red-800'}`}>
                {mockStatus.success ? 'Payment Successful' : 'Payment Failed'}
              </h3>
              <p className={mockStatus.success ? 'text-green-700' : 'text-red-700'}>
                {mockStatus.message}
              </p>
              {mockStatus.success && (
                <div className="mt-4">
                  <button
                    onClick={() => navigate('/')}
                    className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition"
                  >
                    Return to Home
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReversePennyDrop 