import {createClient} from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export const signInUser = async ({email, password}) => {
    const {data, error} = await supabase.auth.signInWithPassword({
        email,
        password,
    })
    if (error) throw error
    return data
}

export const signUpUser = async ({email, password, fullName}) => {
    const {data, error} = await supabase.auth.signUp({
        email,
        password,
        options: {
            data: {
                full_name: fullName,
            },
        },
    })
    if (error) throw error
    return data
}

export const signOutUser = async () => {
    const {error} = await supabase.auth.signOut()
    if (error) throw error
}

export const getCurrentUser = async () => {
    const {data: {user}, error} = await supabase.auth.getUser()
    if (error) throw error
    return user
}

export const updateUserPassword = async (password) => {
    const {data, error} = await supabase.auth.updateUser({password})
    if (error) throw error
    return data
}

export const updateUserData = async ({email, fullName}) => {
    const {data, error} = await supabase.auth.updateUser({
        email: email,
        data: {full_name: fullName},
    })
    if (error) throw error
    return data
}

export const resetUserPassword = async (email, redirectTo) => {
    const {data, error} = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo,
    })
    if (error) throw error
    return data
}

export const signInWithGoogleProvider = async (scopes = 'https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/calendar.readonly') => {
    const {data, error} = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: window.location.origin,
            queryParams: {
                access_type: 'offline',
                prompt: 'consent',
            },
            scopes: scopes,
        },
    })
    if (error) throw error
    return data
}