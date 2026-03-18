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
                    className="fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity border-none"
                    onClick={onClose}
                />
            )}
            <div
                className={`bg-secondary-dark-bg text-white flex flex-col h-full border-r border-dark-border transition-transform duration-300 fixed inset-y-0 left-0 z-50 md:relative md:translate-x-0 ${
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
                        className={`flex items-center gap-3 cursor-pointer ${isCollapsed ? 'md:justify-center md:w-full' : ''}`}
                    >
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0">
                            <img src='/logo.png' alt='Logo'/>
                        </div>
                        <span className={`font-bold text-xl tracking-tight whitespace-nowrap overflow-hidden ${isCollapsed ? 'md:hidden' : ''}`}>
                            KOBA
                        </span>
                    </div>
                    {/* Mobile Close Button */}
                    <button onClick={onClose} className="md:hidden text-gray-400 hover:text-white">
                        <X size={20} />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 space-y-1">
                    {navItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => onTabChange(item.id)}
                            title={isCollapsed ? item.label : ''}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-200 ${
                                activeTab === item.id
                                    ? 'bg-blue-500 text-white shadow-md'
                                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
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
                <div className="p-4 border-t border-dark-border flex flex-col gap-2">
                    <button
                        onClick={() => onTabChange('settings')}
                        title={isCollapsed ? "Settings" : ""}
                        className={`w-full flex items-center gap-3 px-2 py-2 rounded-md transition-all duration-200 group hover:bg-gray-700 ${
                            isCollapsed ? 'md:justify-center' : ''}`}
                    >
                        <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold shrink-0 ${
                            activeTab === 'settings' 
                            ? 'bg-blue-500 border-blue-300 text-white' 
                            : 'bg-gray-600 border-gray-500 text-gray-200'
                        }`}>
                            {(user?.user_metadata?.full_name?.[0] || 'U').toUpperCase()}
                        </div>

                        <div className={`text-left overflow-hidden text-zinc-100 ${isCollapsed ? 'md:hidden' : ''}`}>
                            <p className="text-sm font-medium truncate">
                                {user?.user_metadata?.full_name || user?.email?.split('@')[0]}
                            </p>
                            <p className={`text-xs truncate ${activeTab === 'settings' ? 'text-blue-100' : 'text-gray-400'}`}>
                                {user?.role === 'authenticated' ? 'Pro Member' : 'Free Plan'}
                            </p>
                        </div>
                    </button>

                </div>
            </div>
        </>
    );
}
