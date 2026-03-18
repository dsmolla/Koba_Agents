import { useState, useEffect } from 'react';
import { Menu } from 'lucide-react';
import Sidebar from '../components/dashboard/Sidebar';
import ChatView from '../components/dashboard/ChatView';
import FileManager from '../components/dashboard/FileManager';
import TaskManager from '../components/dashboard/TaskManager';
import SettingsView from '../components/dashboard/SettingsView';
import { useChat } from "../hooks/useChat.js";
import { useAuth } from "../hooks/useAuth.js";
import {listFiles} from "../lib/fileService.js";

function Dashboard() {
    const { user, loading } = useAuth();
    const [activeTab, setActiveTab] = useState('chat');
    const { messages, sendMessage, clearMessages, status, isConnected, isTyping } = useChat();
    const [files, setFiles] = useState([]);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    useEffect(() => {
        if (!user?.id) return;

        const loadFiles = async () => {
            const files = await listFiles(user.id);
            setFiles(files);
        }
        loadFiles();
    }, [user?.id]); // Use user.id — avoids refetch on unrelated user object reference changes

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-950 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    const renderContent = () => {
        switch (activeTab) {
            case 'chat':
                return <ChatView messages={messages} sendMessage={sendMessage} clearMessages={clearMessages} status={status} isConnected={isConnected} isTyping={isTyping} files={files}/>;
            case 'files':
                return <FileManager files={files} setFiles={setFiles}/>;
            case 'tasks':
                return <TaskManager/>;
            case 'settings':
                return <SettingsView user={user}/>;
            default:
                return <ChatView/>;
        }
    };

    return (
        <div className="flex h-screen bg-gray-900 overflow-hidden font-sans relative">
            <Sidebar activeTab={activeTab} onTabChange={(tab) => { setActiveTab(tab); setIsMobileMenuOpen(false); }} user={user} isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} />

            <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <header
                    className="bg-gray-900 border-b border-gray-800 h-16 flex items-center px-4 md:px-8 justify-between shrink-0">
                    <div className="flex items-center gap-3">
                        <button 
                            className="md:hidden p-2 -ml-2 text-gray-400 hover:text-white"
                            onClick={() => setIsMobileMenuOpen(true)}
                        >
                            <Menu size={24} />
                        </button>
                        <h1 className="text-lg md:text-xl font-semibold text-gray-100 capitalize truncate">
                            {activeTab === 'chat' ? 'Chat Assistant' :
                                activeTab === 'files' ? 'File Manager' :
                                    activeTab === 'tasks' ? 'Recursive Tasks' : 'Settings'}
                        </h1>
                    </div>
                </header>

                <div className="flex-1 overflow-auto p-4 md:p-8">
                    <div className="max-w-6xl mx-auto h-full">
                        {renderContent()}
                    </div>
                </div>
            </main>
        </div>
    );
}

export default Dashboard;
