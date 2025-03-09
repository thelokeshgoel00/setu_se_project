import { useNavigate } from 'react-router-dom'
import { resetVerificationFlow } from '../utils/sessionUtils'

const Home = () => {
  const navigate = useNavigate()
  
  const handleStartVerification = (e: React.MouseEvent) => {
    e.preventDefault()
    // Reset verification flow before starting
    resetVerificationFlow()
    navigate('/pan-verification')
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-center mb-8">Welcome to Setu API Integration</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-xl font-semibold mb-4">Verification Flow</h2>
        <p className="text-gray-600 mb-6">
          This application provides a two-step verification process:
        </p>
        <ol className="list-decimal pl-6 mb-6 space-y-2">
          <li className="text-gray-700">
            <span className="font-medium">Step 1:</span> Verify PAN (Permanent Account Number) details using Setu's API
          </li>
          <li className="text-gray-700">
            <span className="font-medium">Step 2:</span> After successful PAN verification, verify bank account using Setu's Reverse Penny Drop API
          </li>
        </ol>
        <div className="mt-6">
          <a 
            href="#"
            onClick={handleStartVerification}
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition text-center"
          >
            Start Verification Process
          </a>
        </div>
      </div>
      
      <div className="mt-12 bg-gray-100 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">About This Application</h2>
        <p className="text-gray-600">
          This application demonstrates integration with Setu's APIs for identity and bank account verification.
          It provides a simple interface to test these APIs and understand their functionality.
        </p>
      </div>
    </div>
  )
}

export default Home 