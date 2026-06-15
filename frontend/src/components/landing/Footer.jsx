import { Link } from 'react-router-dom';
import { Bot, Github, Twitter } from 'lucide-react';

export default function Footer() {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="relative z-10 border-t border-primary-800/40 bg-primary-dark-bg/80 backdrop-blur-md mt-16">
            <div className="max-w-7xl mx-auto px-4 py-12 grid grid-cols-1 md:grid-cols-3 items-center gap-6">

                <div className="flex items-center justify-center md:justify-start gap-3 opacity-80 hover:opacity-100 transition-opacity">
                    <div className="w-8 h-8 rounded-lg bg-primary-700/30 flex items-center justify-center border border-primary-600/30">
                        <Bot className="text-primary-400" size={18} />
                    </div>
                    <span className="font-semibold text-white tracking-wide">Koba Agents</span>
                </div>

                <div className="flex items-center justify-center text-sm font-medium text-gray-400">
                    <Link to="/privacy/policy" className="hover:text-primary-400 transition-colors">Privacy Policy</Link>
                </div>

                <div className="flex items-center justify-center md:justify-end gap-4 text-gray-500">
                    <a href="https://github.com/dsmolla/Koba_Agents" className="hover:text-white transition-colors p-2 rounded-full hover:bg-primary-800/50">
                        <Github size={20} />
                    </a>
                </div>

            </div>

            <div className="text-center pb-8 text-sm text-gray-600 font-light">
                &copy; {currentYear} Koba Agents. Built for Google Workspace.
            </div>
        </footer>
    );
}
