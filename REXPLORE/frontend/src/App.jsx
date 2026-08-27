import { useEffect, useState, lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import { useAuth } from './context/AuthContext'

// Code-split everything below the first authenticated screen: none of these
// are needed to paint the initial Dashboard, so keeping them out of the main
// bundle shrinks the JS the browser must download/parse before first render.
// Dashboard/Login/Register stay eager since one of them is always the first
// screen a visitor sees.
const LibraryPage = lazy(() => import('./pages/LibraryPage'))
const UploadPage = lazy(() => import('./pages/UploadPage'))
const PaperPage = lazy(() => import('./pages/PaperPage'))
const ComparisonPage = lazy(() => import('./pages/ComparisonPage'))
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))

function RouteLoader() {
  return (
    <div className="app-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
      <Loader2 size={26} className="spin" />
    </div>
  )
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem('rexplore-theme') || 'light')
  const { isAuthenticated, loading } = useAuth()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('rexplore-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))

  if (loading) {
    return (
      <div className="auth-boot-loader">
        <Loader2 size={28} className="spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <div className="app-shell">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      <main className="app-main">
        <Suspense fallback={<RouteLoader />}>
          <Routes>
            <Route path="/login" element={<Navigate to="/" replace />} />
            <Route path="/register" element={<Navigate to="/" replace />} />
            <Route path="/" element={<Dashboard onOpenSidebar={() => setSidebarOpen(true)} />} />
            <Route path="/library" element={<LibraryPage onOpenSidebar={() => setSidebarOpen(true)} />} />
            <Route path="/upload" element={<UploadPage onOpenSidebar={() => setSidebarOpen(true)} />} />
            <Route path="/papers/:id" element={<PaperPage onOpenSidebar={() => setSidebarOpen(true)} />} />
            <Route path="/comparison" element={<ComparisonPage onOpenSidebar={() => setSidebarOpen(true)} />} />
            <Route path="/analytics" element={<AnalyticsPage onOpenSidebar={() => setSidebarOpen(true)} />} />
            <Route path="/profile" element={<ProfilePage onOpenSidebar={() => setSidebarOpen(true)} />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}
