import { createContext, useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'

export const AuthContext = createContext({})

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null)
    const [session, setSession] = useState(null)
    const [loading, setLoading] = useState(true)
    const [googleIntegration, setGoogleIntegration] = useState({ connected: false, scopes: "" })

    const fetchGoogleIntegration = useCallback(async (accessToken) => {
        if (!accessToken) return
        try {
            const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/integrations/google`, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
            if (response.ok) {
                const data = await response.json();
                setGoogleIntegration({ connected: data.connected, scopes: data.scopes || "" });
            }
        } catch (error) {
            console.error("Error checking google connection:", error);
        }
    }, [])

    useEffect(() => {
        // Clear integration flag if the user clicked "Back" to return to the app
        // This handles the case where a user starts the flow but cancels by navigating back
        const navEntry = performance.getEntriesByType("navigation")[0];
        if (navEntry && navEntry.type === 'back_forward') {
            localStorage.removeItem('integrating_google');
        }
        // Check active sessions and sets the user
        const checkSession = async () => {
            try {
                const { data: { session } } = await supabase.auth.getSession()
                setSession(session)
                setUser(session?.user ?? null)
                if (session?.access_token) {
                    await fetchGoogleIntegration(session.access_token)
                }
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
                        // Refresh integration status
                        fetchGoogleIntegration(session.access_token);
                    }
                } catch (error) {
                    console.error("Error syncing Google tokens:", error);
                }
            }
        })

        return () => subscription.unsubscribe()
    }, [fetchGoogleIntegration])

    return (
        <AuthContext.Provider value={{ user, session, loading, googleIntegration, fetchGoogleIntegration }}>
            {children}
        </AuthContext.Provider>
    )
}
