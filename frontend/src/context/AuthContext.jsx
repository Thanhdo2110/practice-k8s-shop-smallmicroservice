import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { fetchMe, login as apiLogin, register as apiRegister } from '../api/auth.js'
import { TOKEN_KEY, USER_KEY } from '../lib/config.js'

const AuthContext = createContext(null)

function readJson(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || 'null')
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '')
  const [user, setUser] = useState(() => readJson(USER_KEY))
  const [booting, setBooting] = useState(() => Boolean(localStorage.getItem(TOKEN_KEY)))

  const save = useCallback((nextToken, nextUser) => {
    localStorage.setItem(TOKEN_KEY, nextToken)
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
    setToken(nextToken)
    setUser(nextUser)
  }, [])

  const clear = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken('')
    setUser(null)
  }, [])

  // Token lưu ở localStorage có thể đã hết hạn sau khi pod restart/re-issue secret
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY)
    if (!stored) return undefined
    let ignore = false
    fetchMe(stored)
      .then((fresh) => !ignore && save(stored, fresh))
      .catch(() => !ignore && clear())
      .finally(() => !ignore && setBooting(false))
    return () => {
      ignore = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = useCallback(
    async (username, password) => {
      const data = await apiLogin(username, password)
      save(data.accessToken, data.user)
      return data.user
    },
    [save],
  )

  const value = useMemo(
    () => ({
      token,
      user,
      booting,
      isAuthenticated: Boolean(token),
      isAdmin: user?.role === 'admin',
      login,
      register: apiRegister,
      logout: clear,
    }),
    [token, user, booting, login, clear],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth phải được dùng bên trong <AuthProvider>')
  return context
}
