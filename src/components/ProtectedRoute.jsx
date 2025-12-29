import {Navigate} from 'react-router-dom'
import {useAuth} from "../hooks/useAuth.js";

function ProtectedRoute({children}) {
    const {user, loading} = useAuth()

    if (loading) return <div>Loading...</div>
    if (!user) return <Navigate to="/signup" replace/>

    return children
}

export default ProtectedRoute
