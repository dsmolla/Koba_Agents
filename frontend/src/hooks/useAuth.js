import { useContext } from 'react'
import { AuthContext, GoogleIntegrationContext } from '../context/AuthContext'

export const useAuth = () => {
    return useContext(AuthContext)
}

export const useGoogleIntegration = () => {
    return useContext(GoogleIntegrationContext)
}
