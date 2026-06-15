import Hero from '../../components/landing/Hero';
import Features from '../../components/landing/Features';
import Footer from '../../components/landing/Footer';
import { useAuth } from '../../hooks/useAuth';
import { Navigate } from 'react-router-dom';

export default function Landing() {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen bg-primary-dark-bg flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    if (user) {
        return <Navigate to="/dashboard" replace />;
    }

    return (
        <div className="min-h-screen bg-primary-dark-bg text-blue-50 font-sans overflow-x-hidden selection:bg-primary-500/30">
            {/* Background Effects */}
            <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary-700/20 rounded-full blur-[120px] animate-blob" />
                <div className="absolute top-[20%] right-[-10%] w-[30%] h-[30%] bg-primary-500/10 rounded-full blur-[100px] animate-blob" style={{ animationDelay: '2s' }} />
                <div className="absolute bottom-[-10%] left-[20%] w-[50%] h-[50%] bg-primary-900/20 rounded-full blur-[150px] animate-blob" style={{ animationDelay: '4s' }} />
                <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.03] mix-blend-overlay"></div>
            </div>

            <div className="relative z-10 flex flex-col min-h-screen">
                <Hero />
                <Features />
                <Footer />
            </div>
        </div>
    );
}
