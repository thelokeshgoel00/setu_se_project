import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import PANVerification from './pages/PANVerification'
import ReversePennyDrop from './pages/ReversePennyDrop'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="container py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/pan-verification" element={<PANVerification />} />
          <Route path="/reverse-penny-drop" element={<ReversePennyDrop />} />
          {/* Redirect any other routes to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App 