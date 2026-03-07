import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')).render(
    <StrictMode>
        <BrowserRouter>
            <AuthProvider>
                <App />
                <Toaster
                    position="top-right"
                    toastOptions={{
                        duration: 4000,
                        style: {
                            fontFamily: 'var(--font-family)',
                            fontSize: 'var(--font-size-md)',
                            borderRadius: 'var(--radius-lg)',
                            padding: '12px 16px',
                        },
                        success: {
                            iconTheme: { primary: '#059669', secondary: '#fff' },
                        },
                        error: {
                            iconTheme: { primary: '#DC2626', secondary: '#fff' },
                        },
                    }}
                />
            </AuthProvider>
        </BrowserRouter>
    </StrictMode>
)
