import React from 'react';

const ErrorAlert = ({ message }) => {
    if (!message) return null;

    return (
        <div className="bg-red-100 border border-red-400 text-red-700 px-3 py-1.5 mt-3 rounded-lg relative mb-4" role="alert">
            <span className="block sm:inline">{message}</span>
        </div>
    );
};

export default ErrorAlert;
