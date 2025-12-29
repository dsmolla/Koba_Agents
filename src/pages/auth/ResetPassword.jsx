import React, {useState} from 'react';
import {supabase} from "../../lib/supabase.js";
import AuthLayout from '../../components/auth/AuthLayout';
import AuthInput from '../../components/auth/AuthInput';

const ResetPassword = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const resetPassword = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const {data, error} = await supabase.auth.resetPasswordForEmail(
                    email,
                {
                        redirectTo: 'http://localhost:5173/update-password'
                    }
            )
            if (error) throw new Error(error.message)

        } catch (error) {
            setError(error.message);
            console.error(error)
        } finally {
            setLoading(false);
        }
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
                        className="w-full mt-1 text-white bg-primary-600 hover:bg-primary-700 focus:ring-4 focus:outline-none focus:ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus:ring-primary-800"
                    >
                        {loading ? 'Submitting...' : 'Reset Password'}
                    </button>
                </div>
                <div className="flex justify-center text-sm font-medium mt-5 text-gray-900 dark:text-white">
                    <a href="/login" className="font-semibold text-indigo-400 hover:text-indigo-300">
                        Sign in
                    </a>
                    <div className="border-r border-gray-400 h-6 mx-4"></div>
                    <a href="/signup" className="font-semibold text-indigo-400 hover:text-indigo-300">
                        Sign up
                    </a>
                </div>
            </form>
        </AuthLayout>
    );
};

export default ResetPassword;
