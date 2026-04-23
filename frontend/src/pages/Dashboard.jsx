import { useState, useEffect } from 'react';
import { Menu } from 'lucide-react';
import Sidebar from '../components/dashboard/Sidebar';
import ChatView from '../components/dashboard/ChatView';
import FileManager from '../components/dashboard/FileManager';
import TaskManager from '../components/dashboard/TaskManager';
import SettingsView from '../components/dashboard/SettingsView';
import { useChat } from "../hooks/useChat.js";
import { useAuth } from "../hooks/useAuth.js";
import { listFiles } from "../lib/fileService.js";

function Dashboard() {
    const { user, loading } = useAuth();
    const [activeTab, setActiveTab] = useState('chat');
    const { messages, sendMessage, sendApproval, clearMessages, status, isConnected, isTyping } = useChat();
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
            <div className="min-h-screen bg-primary-dark-bg flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    const renderContent = () => {
        switch (activeTab) {
            case 'chat':
                return <ChatView messages={messages} sendMessage={sendMessage} sendApproval={sendApproval} clearMessages={clearMessages} status={status} isConnected={isConnected} isTyping={isTyping} files={files} />;
            case 'files':
                return <FileManager files={files} setFiles={setFiles} />;
            case 'tasks':
                return <TaskManager />;
            case 'settings':
                return <SettingsView user={user} />;
            default:
                return <ChatView />;
        }
    };

    return (
        <div className="flex h-screen bg-primary-dark-bg overflow-hidden font-sans relative text-blue-50">
            <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary-700/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-primary-900/10 rounded-full blur-[150px]" />
            </div>

            <Sidebar activeTab={activeTab} onTabChange={(tab) => { setActiveTab(tab); setIsMobileMenuOpen(false); }} user={user} isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} />

            <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
                <header
                    className="bg-primary-dark-bg/50 backdrop-blur-md border-b border-dark-border h-16 flex items-center px-4 md:px-8 justify-between shrink-0">
                    <div className="flex items-center gap-3">
                        <button
                            className="md:hidden p-2 -ml-2 text-primary-400 hover:text-primary-300"
                            onClick={() => setIsMobileMenuOpen(true)}
                        >
                            <Menu size={24} />
                        </button>
                        <h1 className="text-lg md:text-xl font-semibold text-gray-100 capitalize truncate">
                            {activeTab === 'chat' ? 'Koba Agents' :
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
