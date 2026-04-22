import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { signUpUser, signInWithGoogleProvider } from '../../lib/supabase.js'
import AuthLayout from '../../components/auth/AuthLayout'
import AuthInput from '../../components/auth/AuthInput'
import GoogleSignInButton from '../../components/auth/GoogleSignInButton'

function Signup() {
    const navigate = useNavigate()
    const inviteRequestEmail = import.meta.env.VITE_INVITE_REQUEST_EMAIL;
    const inviteRequestSubject = import.meta.env.VITE_INVITE_REQUEST_SUBJECT;
    const inviteRequestBody = import.meta.env.VITE_INVITE_REQUEST_BODY;
    const [formData, setFormData] = useState({
        fullName: '',
        email: '',
        invitationCode: '',
        password: '',
        confirmPassword: ''
    })
    const [error, setError] = useState('')
    const [successMessage, setSuccessMessage] = useState('')
    const [loading, setLoading] = useState(false)

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        })
    }

    const signUpWithGoogle = async () => {
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
                fullName: formData.fullName,
                invitationCode: formData.invitationCode
            })
            setSuccessMessage('Confirmation email sent, please verify your email address to complete signing up.')
        } catch (error) {
            setError(error.message)
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    if (successMessage) {
        return (
            <AuthLayout title="Check your email" error={''}>
                <div className="text-center mt-6 space-y-6">
                    <p className="text-gray-300 text-md">{successMessage}</p>
                    <Link
                        to="/login"
                        className="block w-full text-white bg-primary-600 hover:bg-primary-700 focus:ring-4 focus:outline-none focus:ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center transition-colors"
                    >
                        Back to Login
                    </Link>
                </div>
            </AuthLayout>
        )
    }

    return (
        <AuthLayout title="Sign Up" error={error}>
            <form className="mt-4 space-y-4 lg:mt-5 md:space-y-5" onSubmit={handleSubmit}>
                <AuthInput
                    label="Full Name"
                    id="fullName"
                    name="fullName"
                    type="text"
                    required
                    autoComplete="name"
                    value={formData.fullName}
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

                <AuthInput
                    label="Invitation Code"
                    id="invitationCode"
                    name="invitationCode"
                    type="text"
                    required
                    autoComplete="off"
                    value={formData.invitationCode}
                    onChange={handleChange}
                />

                <div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full mt-1 text-white focus:ring-4 focus:outline-none ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center bg-primary-600 hover:bg-primary-700 focus:ring-primary-800"
                    >
                        {loading ? 'Signing up...' : 'Sign Up'}
                    </button>
                </div>
            </form>

            <div className="mt-6">
                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-600" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-secondary-dark-bg text-white">Or continue with</span>
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

            <p className="mt-2 text-center text-sm/6 text-gray-400">
                Signups are currently by invitation only.{' '}
                <a
                    href={`mailto:${inviteRequestEmail}?subject=${encodeURIComponent(inviteRequestSubject)}&body=${encodeURIComponent(inviteRequestBody)}`}
                    className="font-semibold text-indigo-400 hover:text-indigo-300"
                >
                    Request an invite
                </a>
            </p>
        </AuthLayout>
    )
}

export default Signup
