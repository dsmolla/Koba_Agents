import React, {useState} from 'react';
import { Link } from 'react-router-dom';
import {resetUserPassword} from "../../lib/supabase.js";
import AuthLayout from '../../components/auth/AuthLayout';
import AuthInput from '../../components/auth/AuthInput';

const ResetPassword = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');

    const resetPassword = async (e) => {
        e.preventDefault();
        setError('');
        setSuccessMessage('');
        setLoading(true);

        try {
            await resetUserPassword(email, 'http://localhost:5173/update-password');
            setSuccessMessage('If an account exists with this email, a password reset link has been sent.');
        } catch (error) {
            setError(error.message);
            console.error(error)
        } finally {
            setLoading(false);
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
        );
    }

    return (
        <AuthLayout title="Reset Password" error={error}>
            <form className="mt-4 space-y-4 lg:mt-5 md:space-y-5" onSubmit={resetPassword}>
                <AuthInput
                    label="Email"
                    id="email"
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    onChange={(e) => setEmail(e.target.value)}
                />
                
                <div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full mt-1 text-white focus:ring-4 focus:outline-none  font-medium rounded-lg text-sm px-5 py-2.5 text-center bg-primary-600 hover:bg-primary-700 focus:ring-primary-800"
                    >
                        {loading ? 'Submitting...' : 'Reset Password'}
                    </button>
                </div>
                <div className="flex justify-center text-sm font-medium mt-5  text-white">
                    <a href="/login" className="font-semibold text-primary-400 hover:text-primary-300">
                        Sign in
                    </a>
                    <div className="border-r border-dark-border h-6 mx-4"></div>
                    <a href="/signup" className="font-semibold text-primary-400 hover:text-primary-300">
                        Sign up
                    </a>
                </div>
            </form>
        </AuthLayout>
    );
};

export default ResetPassword;