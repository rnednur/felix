import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ToastProvider } from './components/ui/toast'
import { AuthProvider } from './contexts/AuthContext'
import { FilterProvider } from './contexts/FilterContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import Home from './pages/Home'
import DatasetDetail from './pages/DatasetDetail'
import DatasetGroupDetail from './pages/DatasetGroupDetail'
import WorkspaceDetail from './pages/WorkspaceDetail'
import Login from './pages/Login'
import Register from './pages/Register'

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <AuthProvider>
          <FilterProvider>
            <ThemeProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            } />
            <Route path="/datasets/:id" element={
              <ProtectedRoute>
                <DatasetDetail />
              </ProtectedRoute>
            } />
            <Route path="/dataset-groups/:id" element={
              <ProtectedRoute>
                <DatasetGroupDetail />
              </ProtectedRoute>
            } />
            <Route path="/dataset-groups/new" element={
              <ProtectedRoute>
                <DatasetGroupDetail />
              </ProtectedRoute>
            } />
            <Route path="/workspaces/:id" element={
              <ProtectedRoute>
                <WorkspaceDetail />
              </ProtectedRoute>
            } />
          </Routes>
            </ThemeProvider>
          </FilterProvider>
        </AuthProvider>
      </BrowserRouter>
    </ToastProvider>
  )
}

export default App
