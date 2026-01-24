import React from 'react';

export default function AuthInput({label, id, ...props}) {
    return (
        <div>
            <label htmlFor={id} className="block mb-2 text-sm font-medium text-white">
                {label}
            </label>
            <input
                id={id}
                className="
                    text-sm
                    rounded-lg
                    block
                    w-full
                    p-2.5
                    bg-dark-input-bg border-dark-input-border
                    placeholder-dark-input-placeholder text-white
                "
                {...props}
            />
        </div>
    );
}
