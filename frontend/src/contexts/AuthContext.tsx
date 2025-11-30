import React, { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

interface User {
  id: string
  email: string
  username: string
  full_name?: string
  role: 'ADMIN' | 'USER' | 'VIEWER'
  is_active: boolean
  is_verified: boolean
  created_at: string
  last_login_at?: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  // Get tokens from localStorage
  const getAccessToken = () => localStorage.getItem('access_token')
  const getRefreshToken = () => localStorage.getItem('refresh_token')
  const setTokens = (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  }
  const clearTokens = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // Fetch current user
  const fetchCurrentUser = async () => {
    const token = getAccessToken()
    if (!token) {
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Token invalid, try to refresh
        await refreshToken()
      }
    } catch (error) {
      console.error('Failed to fetch user:', error)
      clearTokens()
    } finally {
      setIsLoading(false)
    }
  }

  // Login
  const login = async (email: string, password: string) => {
    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    const data = await response.json()
    setTokens(data.access_token, data.refresh_token)
    await fetchCurrentUser()
    navigate('/')
  }

  // Register
  const register = async (email: string, username: string, password: string, fullName?: string) => {
    const response = await fetch('http://localhost:8000/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        username,
        password,
        full_name: fullName
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }

    // Auto-login after registration
    await login(email, password)
  }

  // Logout
  const logout = async () => {
    const token = getAccessToken()

    if (token) {
      try {
        await fetch('http://localhost:8000/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
      } catch (error) {
        console.error('Logout error:', error)
      }
    }

    clearTokens()
    setUser(null)
    navigate('/login')
  }

  // Refresh token
  const refreshToken = async () => {
    const refresh = getRefreshToken()
    if (!refresh) {
      clearTokens()
      setUser(null)
      return
    }

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: refresh })
      })

      if (response.ok) {
        const data = await response.json()
        setTokens(data.access_token, data.refresh_token)
        await fetchCurrentUser()
      } else {
        clearTokens()
        setUser(null)
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearTokens()
      setUser(null)
    }
  }

  // Load user on mount
  useEffect(() => {
    fetchCurrentUser()
  }, [])

  // Setup token refresh interval (refresh 5 minutes before expiry)
  useEffect(() => {
    if (user) {
      const interval = setInterval(() => {
        refreshToken()
      }, 25 * 60 * 1000) // 25 minutes (tokens expire in 30)

      return () => clearInterval(interval)
    }
  }, [user])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshToken
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
