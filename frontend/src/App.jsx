import { lazy, Suspense } from 'react'
import {BrowserRouter, Routes, Route, Navigate} from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import AuthRoute from './components/AuthRoute'

// Route-level code splitting — each page chunk is downloaded only when first visited.
// Users on /login no longer download Dashboard, dnd-kit, react-markdown, etc.
const Signup = lazy(() => import('./pages/auth/Signup.jsx'))
const Login = lazy(() => import('./pages/auth/Login.jsx'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const UpdatePassword = lazy(() => import('./pages/auth/UpdatePassword.jsx'))
const ResetPassword = lazy(() => import('./pages/auth/ResetPassword.jsx'))
const PrivacyPolicy = lazy(() => import('./pages/legal/PrivacyPolicy.jsx'))

function App() {
    return (
        <BrowserRouter>
            <Suspense fallback={
                <div className="min-h-screen bg-primary-dark-bg flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                </div>
            }>
                <Routes>
                    <Route
                        path="/signup"
                        element={
                            <AuthRoute>
                                <Signup/>
                            </AuthRoute>
                        }
                    />
                    <Route
                        path="/login"
                        element={
                            <AuthRoute>
                                <Login/>
                            </AuthRoute>
                        }
                    />
                    <Route
                        path="/"
                        element={
                            <ProtectedRoute>
                                <Dashboard/>
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/update-password"
                        element={
                        <ProtectedRoute>
                            <UpdatePassword/>
                        </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/reset-password"
                        element={
                        <AuthRoute>
                            <ResetPassword/>
                        </AuthRoute>
                        }
                    />
                    <Route
                        path="/privacy/policy"
                        element={<PrivacyPolicy/>}
                    />
                    <Route path="*" element={<Navigate to="/signup" replace/>}/>
                </Routes>
            </Suspense>
        </BrowserRouter>
    )
}

export default App
