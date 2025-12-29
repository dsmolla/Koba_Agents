import {BrowserRouter, Routes, Route, Navigate} from 'react-router-dom'
import Signup from './pages/auth/Signup.jsx'
import Login from './pages/auth/Login.jsx'
import Dashboard from './pages/Dashboard'
import ProtectedRoute from './components/ProtectedRoute'
import AuthRoute from './components/AuthRoute'
import UpdatePassword from "./pages/auth/UpdatePassword.jsx";
import ResetPassword from "./pages/auth/ResetPassword.jsx";
import {supabase} from "./lib/supabase.js";

supabase.auth.getSession().then(session => {
    console.log(session)
})

function App() {
    return (
        <BrowserRouter>
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
                    path="/dashboard"
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
                <Route path="*" element={<Navigate to="/signup" replace/>}/>
            </Routes>
        </BrowserRouter>
    )
}

export default App
