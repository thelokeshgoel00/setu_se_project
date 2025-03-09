import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import PANVerification from './pages/PANVerification'
import ReversePennyDrop from './pages/ReversePennyDrop'
import Admin from './pages/Admin'
import Login from './pages/Login'
import Register from './pages/Register'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="container py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Protected routes for members only (not admins) */}
            <Route 
              path="/pan-verification" 
              element={
                <ProtectedRoute membersOnly={true}>
                  <PANVerification />
                </ProtectedRoute>
              } 
            />
            
            {/* Protected routes for any authenticated user */}
            <Route 
              path="/reverse-penny-drop" 
              element={
                <ProtectedRoute>
                  <ReversePennyDrop />
                </ProtectedRoute>
              } 
            />
            
            {/* Protected routes for admins */}
            <Route 
              path="/admin" 
              element={
                <ProtectedRoute requireAdmin={true}>
                  <Admin />
                </ProtectedRoute>
              } 
            />
            
            {/* Redirect any other routes to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </AuthProvider>
  )
}

export default App 