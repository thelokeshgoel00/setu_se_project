import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { UserRole } from '../api/authService'
import { resetVerificationFlow } from '../utils/sessionUtils'

const Navbar = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout, isAdmin } = useAuth()
  
  const isActive = (path: string) => {
    return location.pathname === path ? 'bg-blue-700' : ''
  }

  const handleStartVerification = (e: React.MouseEvent) => {
    e.preventDefault()
    // Reset verification flow before starting
    resetVerificationFlow()
    navigate('/pan-verification')
  }

  return (
    <nav className="bg-blue-600 text-white shadow-md">
      <div className="container mx-auto py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="text-xl font-bold">Setu API Integration</Link>
          <div className="flex space-x-4">
            <Link 
              to="/" 
              className={`px-3 py-2 rounded hover:bg-blue-700 transition ${isActive('/')}`}
            >
              Home
            </Link>
            
            {/* Only show Start Verification for non-admin users */}
            {user && user.role === UserRole.MEMBER && (
              <a 
                href="#"
                onClick={handleStartVerification}
                className={`px-3 py-2 rounded hover:bg-blue-700 transition ${isActive('/pan-verification')}`}
              >
                Start Verification
              </a>
            )}
            
            {isAdmin && (
              <Link 
                to="/admin" 
                className={`px-3 py-2 rounded hover:bg-blue-700 transition ${isActive('/admin')}`}
              >
                Admin
              </Link>
            )}
            
            {!user ? (
              <>
                <Link 
                  to="/login" 
                  className={`px-3 py-2 rounded hover:bg-blue-700 transition ${isActive('/login')}`}
                >
                  Login
                </Link>
                <Link 
                  to="/register" 
                  className={`px-3 py-2 rounded hover:bg-blue-700 transition ${isActive('/register')}`}
                >
                  Register
                </Link>
              </>
            ) : (
              <div className="flex items-center space-x-4">
                <span className="text-sm">
                  Welcome, <span className="font-semibold">{user.username}</span>
                  {user.role === UserRole.ADMIN && <span className="ml-1 text-xs bg-yellow-500 text-black px-2 py-0.5 rounded-full">Admin</span>}
                </span>
                <button 
                  onClick={logout}
                  className="px-3 py-2 rounded hover:bg-blue-700 transition"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar