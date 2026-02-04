import React, {useState} from 'react';
import {updateUserPassword} from "../../lib/supabase.js";
import {useNavigate} from "react-router-dom";
import AuthLayout from '../../components/auth/AuthLayout';
import AuthInput from '../../components/auth/AuthInput';

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
            return;
        }

        setError('');
        setLoading(true);

        try {
            const data = await updateUserPassword(password)

            if (data.user) alert("Password updated successfully!")
            else throw new Error('Failed to update password');

            navigate('/')


        } catch (error) {
            setError(error.message)
            console.error(error)
        } finally {
            setLoading(false);
        }
    }


    return (
        <AuthLayout title="Change Password" error={error}>
            <form className="mt-4 space-y-4 lg:mt-5 md:space-y-5" onSubmit={updatePassword}>
                <AuthInput
                    label="New Password"
                    id="password"
                    name="password"
                    type="password"
                    placeholder="••••••••"
                    required
                    minLength='6'
                    onChange={(e) => setPassword(e.target.value)}
                />

                <AuthInput
                    label="Confirm password"
                    id="confirm-password"
                    name="confirm-password"
                    type="password"
                    placeholder="••••••••"
                    required
                    minLength='6'
                    onChange={(e) => setConfirmPassword(e.target.value)}
                />

                <button
                    type="submit"
                    className="w-full text-white focus:ring-4 focus:outline-none ring-primary-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center bg-primary-600 hover:bg-primary-700 focus:ring-primary-800">
                    {loading ? 'Submitting...' : 'Update Password'}
                </button>
            </form>
        </AuthLayout>
    );
};

export default UpdatePassword;