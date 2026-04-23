import React from 'react';
import { Link } from 'react-router-dom';
import ErrorAlert from '../ErrorAlert';

export default function AuthLayout({title, children, error}) {
    return (
        <div className="flex flex-col items-center justify-center px-6 py-8 mx-auto mt-5 lg:py-0 min-h-screen">
            <a href="/" className="flex items-center mb-6 text-2xl font-semibold text-white">
                <img
                    alt='Koba'
                    src='/logo.png'
                    className='mx-auto h-20 w-auto'
                />
                KOBA
            </a>
            <div
                className="
                w-full
                p-6
                rounded-lg
                shadow
                border
                md:mt-0
                sm:max-w-md
                bg-secondary-dark-bg border-dark-border
                sm:p-8">
                <h2 className="mb-1 text-xl font-bold leading-tight tracking-tight md:text-2xl text-white text-center">
                    {title}
                </h2>
                {error && <ErrorAlert message={error}/>}
                {children}
            </div>
            <div className="mt-8 text-center pb-8">
                <p className="text-xs text-gray-500">
                    By continuing, you agree to our{' '}
                    <Link to="/privacy/policy" className="text-gray-400 hover:text-white transition-colors underline underline-offset-2">
                        Privacy Policy
                    </Link>
                </p>
            </div>
        </div>
    );
}
