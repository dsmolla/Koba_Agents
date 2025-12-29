import React, {useState} from 'react';
import {supabase} from "../../lib/supabase.js";
import {Link} from "react-router-dom";
import ErrorAlert from '../../components/ErrorAlert.jsx';

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
        <div className="flex flex-col items-center justify-center px-6 py-8 mx-auto mt-5 lg:py-0">
            <a href="#" className="flex items-center mb-6 text-2xl font-semibold text-gray-900 dark:text-white">
                <img
                    alt='Koba'
                    src='/logo.png'
                    className='mx-auto h-20 w-auto'
                />
                KOBA
            </a>
            <div className="w-full p-6 bg-white rounded-lg shadow dark:border md:mt-0 sm:max-w-md dark:bg-gray-800 dark:border-gray-700 sm:p-8">
                <h2 className="mb-1 text-xl font-bold leading-tight tracking-tight text-gray-900 md:text-2xl dark:text-white">
                    Reset Password
                </h2>
                <ErrorAlert message={error} />
                <form className="mt-4 space-y-4 lg:mt-5 md:space-y-5" onSubmit={resetPassword}>
                    <div>
                        <label htmlFor="email" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">
                            Email
                        </label>
                        <input
                            id="email"
                            type="email"
                            name="email"
                            required
                            autoComplete="email"
                            onChange={(e) => setEmail(e.target.value)}
                            className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                        />
                    </div>
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
            </div>
        </div>

    );
};

export default ResetPassword;