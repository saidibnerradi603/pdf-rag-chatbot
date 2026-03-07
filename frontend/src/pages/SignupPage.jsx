import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AuthForm from '../components/auth/AuthForm'
import { useAuth } from '../context/AuthContext'
import { getErrorMessage } from '../utils/helpers'
import toast from 'react-hot-toast'

export default function SignupPage() {
    const { signup } = useAuth()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)

    async function handleSignup(email, password) {
        setLoading(true)
        try {
            await signup(email, password)
            toast.success('Account created! Please sign in.')
            navigate('/login', { replace: true })
        } catch (err) {
            toast.error(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }

    return <AuthForm mode="signup" onSubmit={handleSignup} loading={loading} />
}
