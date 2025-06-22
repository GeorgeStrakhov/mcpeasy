import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { Toaster } from '@/components/ui/toaster'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ClientDetailPage from './pages/ClientDetailPage'
import AnalyticsPage from './pages/AnalyticsPage'
import AdminManagementPage from './pages/AdminManagementPage'
import SystemMonitoringPage from './pages/SystemMonitoringPage'
import NotFoundPage from './pages/NotFoundPage'
import Layout from './components/Layout'

function App() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/clients/:clientId" element={<ClientDetailPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/admins" element={<AdminManagementPage />} />
          <Route path="/monitoring" element={<SystemMonitoringPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Layout>
      <Toaster />
    </Router>
  )
}

export default App