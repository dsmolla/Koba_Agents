import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = {hasError: false, error: null};
    }

    static getDerivedStateFromError(error) {
        return {hasError: true, error};
    }

    componentDidCatch(error, errorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div
                    className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-4">
                    <div className="max-w-md w-full text-center space-y-4">
                        <h1 className="text-3xl font-bold text-red-600">Something went wrong.</h1>
                        <p className="text-lg">We're sorry, but an unexpected error occurred.</p>
                        <pre
                            className="text-xs text-left bg-gray-200 dark:bg-gray-800 p-4 rounded overflow-auto max-h-40">
                {this.state.error?.toString()}
             </pre>
                        <button
                            onClick={() => window.location.reload()}
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                        >
                            Reload Page
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
