import { Link } from 'react-router-dom';
import { ArrowRight, Bot, Sparkles } from 'lucide-react';

export default function Hero() {
    return (
        <section className="relative flex-1 flex flex-col items-center justify-center min-h-[90vh] px-4 pt-20">
            {/* Header/Nav built into the Hero section for a clean, unified look */}
            <nav className="absolute top-0 w-full flex items-center justify-between p-6 max-w-7xl mx-auto">
                <div className="flex items-center gap-2">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center">
                        <img
                            alt='Koba'
                            src='/logo.svg'
                        />
                    </div>
                    <span className="text-xl font-bold tracking-tight text-white">Koba Agents</span>
                </div>
                <div className="flex items-center gap-4">
                    <Link to="/login" className="text-sm font-medium text-gray-300 hover:text-white transition-colors">
                        Sign In
                    </Link>
                    <Link to="/signup" className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-medium transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)] hover:shadow-[0_0_25px_rgba(37,99,235,0.6)]">
                        Get Started
                    </Link>
                </div>
            </nav>

            <div className="max-w-4xl mx-auto text-center z-10 animate-fade-in opacity-0">
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-900/30 border border-primary-500/20 text-primary-300 text-sm font-medium mb-8">
                    <Sparkles size={16} />
                    <span>Next-Gen Google Workspace Assistant</span>
                </div>

                <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 text-transparent bg-clip-text bg-gradient-to-br from-white via-blue-100 to-primary-400 leading-tight">
                    Your Autonomous <br className="hidden md:block" /> Workspace Brain
                </h1>

                <p className="text-lg md:text-xl text-gray-400 mb-10 max-w-2xl mx-auto font-light leading-relaxed">
                    Delegate your emails, calendar, and documents to a swarm of specialized AI agents. Reclaim your time with intelligent auto-replies, smart scheduling, and automated workflows.
                </p>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <Link to="/signup" className="w-full sm:w-auto px-8 py-4 rounded-xl bg-primary-600 hover:bg-primary-500 text-white font-medium text-lg transition-all shadow-[0_0_20px_rgba(37,99,235,0.5)] hover:shadow-[0_0_35px_rgba(37,99,235,0.7)] flex items-center justify-center gap-2 group">
                        Start Delegating
                        <ArrowRight className="group-hover:translate-x-1 transition-transform" size={20} />
                    </Link>
                    <a href="#features" className="w-full sm:w-auto px-8 py-4 rounded-xl bg-primary-900/40 hover:bg-primary-800/50 border border-primary-700/50 text-white font-medium text-lg transition-all flex items-center justify-center">
                        Explore Features
                    </a>
                </div>
            </div>

            {/* Decorative Mockup / Abstract visual below hero text */}
            <div className="mt-16 w-full max-w-4xl mx-auto relative animate-slide-up opacity-0" style={{ animationDelay: '0.2s' }}>
                <div className="bg-primary-900/20 rounded-t-3xl border border-b-0 border-primary-500/20 backdrop-blur-md overflow-hidden relative shadow-2xl pb-16">
                    <div className="absolute top-0 w-full h-px bg-gradient-to-r from-transparent via-primary-400/50 to-transparent" />
                    <div className="p-6 md:p-10 flex flex-col gap-6">
                        {/* Human Message */}
                        <div className="flex justify-end animate-fade-in opacity-0" style={{ animationDelay: '0.6s' }}>
                            <div className="max-w-[90%] md:max-w-[75%] bg-primary-600 text-white rounded-2xl rounded-tr-sm px-5 py-4 shadow-md">
                                <p className="text-[15px] md:text-base leading-relaxed">
                                    Find emails from linkedin job alerts extract Job title, company, location, job url then create a new google sheets and add the data there
                                </p>
                            </div>
                        </div>

                        {/* Bot Message */}
                        <div className="flex justify-start items-start gap-4 animate-fade-in opacity-0" style={{ animationDelay: '1.4s' }}>
                            <div className="w-10 h-10 rounded-full bg-primary-800/50 flex items-center justify-center border border-primary-500/30 shrink-0 mt-1">
                                <Bot className="text-primary-400" size={20} />
                            </div>
                            <div className="max-w-[90%] md:max-w-[75%] bg-[#0F1840]/80 border border-primary-700/30 text-gray-200 rounded-2xl rounded-tl-sm px-5 py-4 shadow-md">
                                <p className="text-[15px] md:text-base leading-relaxed mb-3">
                                    I found 12 recent LinkedIn job alerts in your inbox. I've extracted the data and created a new Google Sheet for you.
                                </p>
                                <div className="flex items-center gap-3 p-3 bg-primary-900/40 rounded-xl border border-primary-700/30 mt-2">
                                    {/* <div className="w-8 h-8 rounded bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30 shrink-0">
                                        <svg className="w-4 h-4 text-emerald-400" fill="currentColor" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 9h-2V7h-2v5H6v2h2v5h2v-5h2v-2z" /></svg>
                                    </div> */}
                                    <span className="text-sm font-medium text-emerald-400 truncate">LinkedIn Job Alerts.xlsx</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                {/* Fade out gradient at bottom to blend with next section */}
                <div className="absolute bottom-0 w-full h-32 bg-gradient-to-t from-primary-dark-bg to-transparent z-10 pointer-events-none" />
            </div>
        </section>
    );
}
