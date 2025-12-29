import {useState, useEffect} from 'react'
import {supabase} from '../lib/supabase'

function Dashboard() {
    const [user, setUser] = useState(null)

    useEffect(() => {
        supabase.auth.getUser().then(({data: {user}}) => {
            setUser(user)
        })
    }, [])

    const getUserDisplayName = () => {
        if (!user) return ''

        const firstName = user.user_metadata?.first_name
        const lastName = user.user_metadata?.last_name

        if (firstName && lastName) {
            return `${firstName} ${lastName} (${user.email})`
        } else if (firstName) {
            return `${firstName} (${user.email})`
        }

        return user.email
    }

    return (
        <div>
            <h1 className='text-green-400'>Welcome, {getUserDisplayName()}</h1>
        </div>
    )
}

export default Dashboard
