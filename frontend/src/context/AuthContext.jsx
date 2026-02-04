import { createContext, useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export const AuthContext = createContext({})

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null)
    const [session, setSession] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Check active sessions and sets the user
        const checkSession = async () => {
            try {
                const { data: { session } } = await supabase.auth.getSession()
                setSession(session)
                setUser(session?.user ?? null)
            } catch (error) {
                console.error("Error checking session:", error)
            } finally {
                setLoading(false)
            }
        }

        checkSession()

        // Listen for changes on auth state (logged in, signed out, etc.)
        const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
            setSession(session)
            setUser(session?.user ?? null)
            setLoading(false)

            const isIntegrating = localStorage.getItem('integrating_google') === 'true';

            if (session?.provider_token && session?.access_token && isIntegrating) {
                try {
                    const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
                    const response = await fetch(`${apiUrl}/integrations/google`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${session.access_token}`
                        },
                        body: JSON.stringify({
                            token: session.provider_token,
                            refresh_token: session.provider_refresh_token,
                        }),
                    });

                    if (!response.ok) {
                        console.error("Failed to sync Google tokens:", await response.text());
                    } else {
                        // Only clear the flag if sync was successful or attempted
                        localStorage.removeItem('integrating_google');
                    }
                } catch (error) {
                    console.error("Error syncing Google tokens:", error);
                }
            }
        })

        return () => subscription.unsubscribe()
    }, [])

    return (
        <AuthContext.Provider value={{ user, session, loading }}>
            {children}
        </AuthContext.Provider>
    )
}
