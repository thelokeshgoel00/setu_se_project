import { Link, useLocation } from 'react-router-dom'

const Navbar = () => {
  const location = useLocation()
  
  const isActive = (path: string) => {
    return location.pathname === path ? 'bg-blue-700' : ''
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
            <Link 
              to="/pan-verification" 
              className={`px-3 py-2 rounded hover:bg-blue-700 transition ${isActive('/pan-verification')}`}
            >
              Start Verification
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar 