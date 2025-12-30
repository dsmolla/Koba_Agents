import React, {useState} from 'react'
import {useNavigate, Link} from 'react-router-dom'
import {signUpUser, signInWithGoogleProvider} from '../../lib/supabase.js'
import AuthLayout from '../../components/auth/AuthLayout'
import AuthInput from '../../components/auth/AuthInput'
import GoogleSignInButton from '../../components/auth/GoogleSignInButton'

function Signup() {
    const navigate = useNavigate()
    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        email: '',
        password: '',
        confirmPassword: ''
    })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        })
    }

    const signUpWithGoogle = async() => {
        try {
            await signInWithGoogleProvider()
        } catch (error) {
            console.error(error)
            setError(error.message)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')

        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match')
            return
        }

        setLoading(true)

        try {
            await signUpUser({
                email: formData.email,
                password: formData.password,
                firstName: formData.firstName,
                lastName: formData.lastName
            })
            navigate('/dashboard')
        } catch (error) {
            setError(error.message)
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <AuthLayout title="Sign Up" error={error}>
            <form className="mt-4 space-y-4 lg:mt-5 md:space-y-5" onSubmit={handleSubmit}>
                <AuthInput
                    label="First Name"
                    id="firstName"
                    name="firstName"
                    type="text"
                    required
                    autoComplete="first-name"
                    value={formData.firstName}
                    onChange={handleChange}
                />

                <AuthInput
                    label="Last Name"
                    id="lastName"
                    name="lastName"
                    type="text"
                    required
                    autoComplete="last-name"
                    value={formData.lastName}
                    onChange={handleChange}
                />

                <AuthInput
                    label="Email"
                    id="email"
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    value={formData.email}
                    onChange={handleChange}
                />

                <AuthInput
                    label="Password"
                    id="password"
                    name="password"
                    type="password"
                    required
                    autoComplete="new-password"
                    value={formData.password}
                    onChange={handleChange}
                />

                <AuthInput
                    label="Confirm Password"
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    required
                    autoComplete="new-password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                />

                <div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full mt-1 text-white bg-primary-600 hover:bg-primary-700 focus:ring-4 focus:outline-none focus:ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus:ring-primary-800"
                    >
                        {loading ? 'Signing up...' : 'Sign Up'}
                    </button>
                </div>
            </form>

            <div className="mt-6">
                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-600"/>
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="bg-white text-gray-900 px-2 dark:bg-gray-800 dark:text-white">Or continue with</span>
                    </div>
                </div>

                <GoogleSignInButton onClick={signUpWithGoogle} text="Sign up with Google" />
            </div>

            <p className="mt-5 text-center text-sm/6 text-gray-400">
                Have an account? {' '}
                <Link
                    to="/login"
                    className="font-semibold text-indigo-400 hover:text-indigo-300"
                >
                    Login!
                </Link>
            </p>
        </AuthLayout>
    )
}

export default Signup
