import {useState} from 'react';
import {MessageSquare, Folder, Calendar, X} from 'lucide-react';

export default function Sidebar({activeTab, onTabChange, user, isOpen = false, onClose}) {
    const [isCollapsed, setIsCollapsed] = useState(true);

    const navItems = [
        {id: 'chat', label: 'Chat Assistant', icon: MessageSquare},
        {id: 'files', label: 'File Manager', icon: Folder},
        {id: 'tasks', label: 'Recursive Tasks', icon: Calendar},
    ];

    return (
        <>
            {/* Mobile Backdrop */}
            {isOpen && (
                <div 
                    className="fixed inset-0 bg-slate-950/80 z-40 md:hidden transition-opacity border-none backdrop-blur-sm"
                    onClick={onClose}
                />
            )}
            <div
                className={`bg-slate-950/40 backdrop-blur-md text-blue-50 flex flex-col h-full border-r border-blue-900/30 transition-transform duration-300 fixed inset-y-0 left-0 z-50 md:relative md:translate-x-0 ${
                    isOpen ? 'translate-x-0' : '-translate-x-full'
                } w-64 ${isCollapsed ? 'md:w-20' : 'md:w-64'}`}
            >
                {/* Header */}
                <div className={`p-6 flex items-center justify-between ${isCollapsed ? 'md:justify-center' : ''}`}>
                    <div 
                        onClick={() => {
                            if (window.innerWidth >= 768) {
                                setIsCollapsed(!isCollapsed);
                            }
                        }}
                        className={`flex items-center gap-3 cursor-pointer group ${isCollapsed ? 'md:justify-center md:w-full' : ''}`}
                    >
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shrink-0 shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
                            <MessageSquare className="w-5 h-5 text-white" />
                        </div>
                        <span className={`font-bold text-xl tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-100 to-blue-400 whitespace-nowrap overflow-hidden ${isCollapsed ? 'md:hidden' : ''}`}>
                            KOBA
                        </span>
                    </div>
                    {/* Mobile Close Button */}
                    <button onClick={onClose} className="md:hidden text-blue-400 hover:text-blue-300 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 space-y-2">
                    {navItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => onTabChange(item.id)}
                            title={isCollapsed ? item.label : ''}
                            className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-300 ${
                                activeTab === item.id
                                    ? 'bg-blue-600/20 text-blue-100 shadow-[0_0_15px_rgba(37,99,235,0.15)] border border-blue-500/30'
                                    : 'text-blue-200/70 hover:bg-blue-900/30 hover:text-blue-100 border border-transparent'
                            } ${isCollapsed ? 'md:justify-center' : ''}`}
                        >
                            <item.icon size={20} className="shrink-0"/>
                            <span className={`font-medium whitespace-nowrap overflow-hidden ${isCollapsed ? 'md:hidden' : ''}`}>
                                {item.label}
                            </span>
                        </button>
                    ))}
                </nav>

                {/* Footer / User Profile & Toggle */}
                <div className="p-4 border-t border-blue-900/30 flex flex-col gap-2">
                    <button
                        onClick={() => onTabChange('settings')}
                        title={isCollapsed ? "Settings" : ""}
                        className={`w-full flex items-center gap-3 px-2 py-2 rounded-xl transition-all duration-300 group hover:bg-blue-900/40 ${
                            isCollapsed ? 'md:justify-center' : ''}`}
                    >
                        <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold shrink-0 shadow-inner ${
                            activeTab === 'settings' 
                            ? 'bg-blue-600/30 border-blue-400/50 text-blue-100' 
                            : 'bg-slate-800/50 border-blue-900/50 text-blue-300 group-hover:border-blue-700/50'
                        }`}>
                            {(user?.user_metadata?.full_name?.[0] || 'U').toUpperCase()}
                        </div>

                        <div className={`text-left overflow-hidden ${isCollapsed ? 'md:hidden' : ''}`}>
                            <p className="text-sm font-medium truncate text-blue-100">
                                {user?.user_metadata?.full_name || user?.email?.split('@')[0]}
                            </p>
                            <p className={`text-xs truncate ${activeTab === 'settings' ? 'text-blue-300' : 'text-blue-400/60'}`}>
                                {user?.role === 'authenticated' ? 'Pro Member' : 'Free Plan'}
                            </p>
                        </div>
                    </button>

                </div>
            </div>
        </>
    );
}
