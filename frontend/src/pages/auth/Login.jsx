import React, {useState} from 'react'
import {useNavigate, Link} from 'react-router-dom'
import {signInUser, signInWithGoogleProvider} from '../../lib/supabase.js'
import AuthLayout from '../../components/auth/AuthLayout'
import AuthInput from '../../components/auth/AuthInput'
import GoogleSignInButton from '../../components/auth/GoogleSignInButton'

function Login() {
    const navigate = useNavigate()
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        })
    }

    const signInWithGoogle = async() => {
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
        setLoading(true)

        try {
            await signInUser({
                email: formData.email,
                password: formData.password
            })
            navigate('/')
        } catch (error) {
            setError(error.message)
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <AuthLayout title="Login" error={error}>
            <form className="mt-4 space-y-4 lg:mt-5 md:space-y-5" onSubmit={handleSubmit}>
                <AuthInput
                    label="Email address"
                    id="email"
                    name="email"
                    type="email"
                    required
                    autoComplete='email'
                    value={formData.email}
                    onChange={handleChange}
                />

                <div>
                    <div className="flex items-center justify-between mb-2">
                        <label htmlFor="password" className="block text-sm font-medium text-gray-900 dark:text-white">
                            Password
                        </label>
                        <div className="text-sm">
                            <Link to='/reset-password' className="font-semibold text-indigo-400 hover:text-indigo-300">
                                Forgot password?
                            </Link>
                        </div>
                    </div>
                    <input
                        id="password"
                        type="password"
                        name="password"
                        required
                        autoComplete='current-password'
                        value={formData.password}
                        onChange={handleChange}
                        className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                    />
                </div>
                
                <button
                    type='submit'
                    disabled={ loading }
                    className="w-full mt-1 text-white bg-primary-600 hover:bg-primary-700 focus:ring-4 focus:outline-none focus:ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus:ring-primary-900"
                >
                    {loading ? 'Logging in...' : 'Login'}
                </button>
            </form>

            <div className="mt-6">
                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-600" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="bg-white text-gray-900 px-2 dark:bg-gray-800 dark:text-white">Or continue with</span>
                    </div>
                </div>

                <GoogleSignInButton onClick={signInWithGoogle} />
            </div>

            <p className="mt-5 text-center text-sm/6 text-gray-400">
                Don't have an account? {' '}
                <Link
                    to="/signup"
                    className="font-semibold text-indigo-400 hover:text-indigo-300"
                >
                    Sign up!
                </Link>
            </p>
        </AuthLayout>
    )
}

export default Login
