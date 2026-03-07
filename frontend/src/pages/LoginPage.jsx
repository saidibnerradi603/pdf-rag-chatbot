import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import AuthForm from '../components/auth/AuthForm'
import { getErrorMessage } from '../utils/helpers'
import toast from 'react-hot-toast'

export default function LoginPage() {
    const { login } = useAuth()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)

    async function handleLogin(email, password) {
        setLoading(true)
        try {
            await login(email, password)
            toast.success('Welcome back!')
            navigate('/', { replace: true })
        } catch (err) {
            toast.error(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }

    return <AuthForm mode="login" onSubmit={handleLogin} loading={loading} />
}
