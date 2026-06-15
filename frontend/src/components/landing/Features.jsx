import { Mail, Calendar, FileText, Database, GitMerge, Shield } from 'lucide-react';

export default function Features() {
    const features = [
        {
            title: "Autonomous Gmail Webhooks",
            description: "Process incoming emails in the background. Define dynamic rules for auto-replies, and let the AI draft context-aware responses instantly.",
            icon: <Mail className="text-blue-400" size={24} />,
            colSpan: "col-span-1 md:col-span-2",
            bg: "bg-gradient-to-br from-blue-900/40 to-primary-900/20"
        },
        {
            title: "Smart Scheduling",
            description: "Manage your calendar natively. The agent checks your availability and schedules meetings autonomously.",
            icon: <Calendar className="text-purple-400" size={24} />,
            colSpan: "col-span-1",
            bg: "bg-gradient-to-br from-purple-900/40 to-primary-900/20"
        },
        {
            title: "Docs & Sheets Integration",
            description: "Analyze vast amounts of data in spreadsheets or draft extensive documents without leaving the chat interface.",
            icon: <FileText className="text-emerald-400" size={24} />,
            colSpan: "col-span-1",
            bg: "bg-gradient-to-br from-emerald-900/40 to-primary-900/20"
        },
        {
            title: "Supervisor Architecture",
            description: "A centralized master agent routes your natural language requests to specialized sub-agents optimized for specific APIs.",
            icon: <GitMerge className="text-orange-400" size={24} />,
            colSpan: "col-span-1 md:col-span-2",
            bg: "bg-gradient-to-br from-orange-900/40 to-primary-900/20"
        },
        {
            title: "Long-Term Memory",
            description: "The agent securely learns your preferences and references past interactions to provide deeply personalized assistance.",
            icon: <Database className="text-pink-400" size={24} />,
            colSpan: "col-span-1 md:col-span-2",
            bg: "bg-gradient-to-br from-pink-900/40 to-primary-900/20"
        },
        {
            title: "Enterprise Security",
            description: "Built on Supabase with strict Row Level Security (RLS) and encrypted OAuth tokens. Your data is isolated and protected.",
            icon: <Shield className="text-slate-400" size={24} />,
            colSpan: "col-span-1",
            bg: "bg-gradient-to-br from-slate-800/40 to-primary-900/20"
        }
    ];

    return (
        <section id="features" className="relative z-10 py-24 px-4 max-w-7xl mx-auto w-full">
            <div className="text-center mb-16 animate-slide-up opacity-0" style={{ animationDelay: '0.3s' }}>
                <h2 className="text-3xl md:text-5xl font-bold mb-6 text-white tracking-tight">Everything you need. <br className="hidden md:block"/> All in one place.</h2>
                <p className="text-gray-400 max-w-2xl mx-auto text-lg">
                    Stop context switching between tabs. Let specialized agents handle the heavy lifting while you focus on what matters.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-slide-up opacity-0" style={{ animationDelay: '0.5s' }}>
                {features.map((feature, idx) => (
                    <div 
                        key={idx} 
                        className={`rounded-3xl p-8 border border-primary-700/30 backdrop-blur-md transition-all hover:border-primary-500/50 hover:shadow-[0_0_30px_rgba(37,99,235,0.15)] group ${feature.colSpan} ${feature.bg}`}
                    >
                        <div className="w-14 h-14 rounded-2xl bg-black/40 flex items-center justify-center mb-6 border border-white/5 group-hover:scale-110 transition-transform">
                            {feature.icon}
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-3">{feature.title}</h3>
                        <p className="text-gray-400 leading-relaxed text-lg">
                            {feature.description}
                        </p>
                    </div>
                ))}
            </div>
        </section>
    );
}
