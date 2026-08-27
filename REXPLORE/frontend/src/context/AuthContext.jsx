import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import api, { setAuthToken } from '../api'

const AuthContext = createContext(null)
const TOKEN_KEY = 'rexplore-token'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setAuthToken(token)
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    api.me()
      .then((r) => setUser(r.data))
      .catch(() => {
        // Token invalid/expired - clear it silently.
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  const applySession = useCallback((data) => {
    localStorage.setItem(TOKEN_KEY, data.access_token)
    setAuthToken(data.access_token)
    setToken(data.access_token)
    setUser(data.user)
  }, [])

  const updateUser = useCallback((updatedUser) => {
    setUser(updatedUser)
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await api.login(email, password)
    applySession(res.data)
    return res.data.user
  }, [applySession])

  const register = useCallback(async (fullName, email, password, confirmPassword) => {
    const res = await api.register(fullName, email, password, confirmPassword)
    applySession(res.data)
    return res.data.user
  }, [applySession])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      // Even if the network call fails, clear the local session.
    }
    localStorage.removeItem(TOKEN_KEY)
    setAuthToken(null)
    setToken(null)
    setUser(null)
  }, [])

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    register,
    logout,
    updateUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
