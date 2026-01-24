import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase.js'

export function useAuth() {
    const [loading, setLoading] = useState(true)
    const [user, setUser] = useState(null)

    useEffect(() => {
        supabase.auth.getUser().then(({ data: { user } }) => {
            setUser(user)
            setLoading(false)
        })

        const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, session) => {
            setUser(session?.user ?? null)

            if (session?.provider_token && session?.access_token) {
                try {
                    console.log("Sending Google tokens to backend...");
                    const response = await fetch('http://localhost:8000/integrations/google', {
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

                    if (response.ok) {
                        console.log("Successfully synced Google tokens with backend.");
                    } else {
                        console.error("Failed to sync Google tokens:", await response.text());
                    }
                } catch (error) {
                    console.error("Error syncing Google tokens:", error);
                }
            }
        })

        return () => subscription.unsubscribe()
    }, [])

    return { user, loading }
}