import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI } from '../api/auth'
import { setAccessToken } from '../api/axios'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        let cancelled = false

        async function tryRefresh() {
            try {
                const refreshRes = await authAPI.refresh()
                setAccessToken(refreshRes.data.access_token)
                const meRes = await authAPI.me()
                if (!cancelled) setUser(meRes.data)
            } catch {
                setAccessToken(null)
            } finally {
                if (!cancelled) setLoading(false)
            }
        }

        tryRefresh()
        return () => { cancelled = true }
    }, [])

    const login = useCallback(async (email, password) => {
        const loginRes = await authAPI.login({ email, password })
        setAccessToken(loginRes.data.access_token)
        const meRes = await authAPI.me()
        setUser(meRes.data)
        return meRes.data
    }, [])

    const signup = useCallback(async (email, password) => {
        const res = await authAPI.signup({ email, password })
        return res.data
    }, [])

    const logout = useCallback(async () => {
        try {
            await authAPI.logout()
        } catch {
            // ignore
        }
        setAccessToken(null)
        setUser(null)
        toast.success('Logged out successfully')
    }, [])

    const value = {
        user,
        loading,
        login,
        signup,
        logout,
        isAuthenticated: !!user,
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
