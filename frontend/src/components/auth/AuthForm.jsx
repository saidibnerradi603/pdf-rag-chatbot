import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { HiOutlineEye, HiOutlineEyeSlash } from 'react-icons/hi2'
import { FiFileText } from 'react-icons/fi'

export default function AuthForm({ mode, onSubmit, loading }) {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [errors, setErrors] = useState({})

    const isLogin = mode === 'login'

    function validate() {
        const errs = {}
        if (!email.trim()) errs.email = 'Email is required'
        else if (!/\S+@\S+\.\S+/.test(email)) errs.email = 'Invalid email format'

        if (!password) errs.password = 'Password is required'
        else if (!isLogin) {
            if (password.length < 8) errs.password = 'At least 8 characters'
            else if (!/[A-Z]/.test(password)) errs.password = 'Needs an uppercase letter'
            else if (!/[a-z]/.test(password)) errs.password = 'Needs a lowercase letter'
            else if (!/[0-9]/.test(password)) errs.password = 'Needs a digit'
            else if (!/[^A-Za-z0-9]/.test(password)) errs.password = 'Needs a special character'
        }

        setErrors(errs)
        return Object.keys(errs).length === 0
    }

    async function handleSubmit(e) {
        e.preventDefault()
        if (!validate()) return
        onSubmit(email, password)
    }

    return (
        <div className="auth-page">
            <motion.div
                className="auth-card"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
            >
                <div className="auth-header">
                    <div className="auth-logo">
                        <FiFileText />
                    </div>
                    <h1>{isLogin ? 'Welcome back' : 'Create account'}</h1>
                    <p>
                        {isLogin
                            ? 'Sign in to continue to PDF RAG Chat'
                            : 'Sign up to get started with PDF RAG Chat'}
                    </p>
                </div>

                <form className="auth-form" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            className={`form-input ${errors.email ? 'error' : ''}`}
                            placeholder="you@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            autoComplete="email"
                            autoFocus
                        />
                        {errors.email && <span className="form-error">{errors.email}</span>}
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <div className="password-input-wrapper">
                            <input
                                id="password"
                                type={showPassword ? 'text' : 'password'}
                                className={`form-input ${errors.password ? 'error' : ''}`}
                                placeholder={isLogin ? 'Enter your password' : 'Min. 8 characters'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                autoComplete={isLogin ? 'current-password' : 'new-password'}
                            />
                            <button
                                type="button"
                                className="password-toggle"
                                onClick={() => setShowPassword(!showPassword)}
                                tabIndex={-1}
                            >
                                {showPassword ? <HiOutlineEyeSlash /> : <HiOutlineEye />}
                            </button>
                        </div>
                        {errors.password && <span className="form-error">{errors.password}</span>}
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary btn-full btn-lg"
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <span className="spinner spinner-sm spinner-white" />
                                {isLogin ? 'Signing in...' : 'Creating account...'}
                            </>
                        ) : (
                            isLogin ? 'Sign in' : 'Create account'
                        )}
                    </button>
                </form>

                <div className="auth-footer">
                    {isLogin ? (
                        <span>
                            Don&apos;t have an account?{' '}
                            <Link to="/signup">Sign up</Link>
                        </span>
                    ) : (
                        <span>
                            Already have an account?{' '}
                            <Link to="/login">Sign in</Link>
                        </span>
                    )}
                </div>
            </motion.div>
        </div>
    )
}
