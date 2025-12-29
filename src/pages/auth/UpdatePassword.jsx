import React, {useState} from 'react';
import {supabase} from "../../lib/supabase.js";
import {useNavigate} from "react-router-dom";
import ErrorAlert from '../../components/ErrorAlert.jsx';

const UpdatePassword = () => {
    const navigate = useNavigate()
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const updatePassword = async (e) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            setError("Passwords don't match");
            console.error("Password don't match");
            return;
        }

        setError('');
        setLoading(true);

        try {
            const {data, error} = await supabase.auth.updateUser({ password: password })

            if (data.user) alert("Password updated successfully!")
            else throw new Error('Failed to update password');

            if (error) throw new Error(error.message)

            navigate('/dashboard')


        } catch (error) {
            setError(error.message)
            console.error(error)
        } finally {
            setLoading(false);
        }
    }


    return (
            <div className="flex flex-col items-center justify-center px-6 py-8 mx-auto md:h-screen lg:py-0">
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
                        Change Password
                    </h2>
                    <ErrorAlert message={error} />
                    <form className="mt-4 space-y-4 lg:mt-5 md:space-y-5" onSubmit={updatePassword}>
                        <div>
                            <label
                                htmlFor="password"
                                className="block mb-2 text-sm font-medium text-gray-900 dark:text-white"
                            >
                                New Password
                            </label>
                            <input
                                type="password"
                                name="password"
                                id="password"
                                placeholder="••••••••"
                                className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                                required
                                minLength='6'
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                        <div>
                            <label
                                htmlFor="confirm-password"
                                className="block mb-2 text-sm font-medium text-gray-900 dark:text-white"
                            >
                                Confirm password
                            </label>
                            <input
                                type="password"
                                name="confirm-password"
                                id="confirm-password"
                                placeholder="••••••••"
                                className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                                required
                                minLength='6'
                                onChange={(e) => setConfirmPassword(e.target.value)}
                            />
                        </div>
                        <button
                            type="submit"
                            className="w-full text-white bg-primary-600 hover:bg-primary-700 focus:ring-4 focus:outline-none focus:ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus:ring-primary-800">
                            {loading ? 'Submitting...' : 'Update Password'}
                        </button>
                    </form>
                </div>
            </div>
    );
};

export default UpdatePassword;