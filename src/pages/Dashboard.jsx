import {useState, useEffect} from 'react';
import {supabase} from '../lib/supabase';
import Sidebar from '../components/dashboard/Sidebar';
import ChatView from '../components/dashboard/ChatView';
import FileManager from '../components/dashboard/FileManager';
import TaskManager from '../components/dashboard/TaskManager';
import SettingsView from '../components/dashboard/SettingsView';

function Dashboard() {
    const [user, setUser] = useState(null);
    const [activeTab, setActiveTab] = useState('chat');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const getUser = async () => {
            const {data: {user}} = await supabase.auth.getUser();
            setUser(user);
            setLoading(false);
        };
        getUser();
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    const renderContent = () => {
        switch (activeTab) {
            case 'chat':
                return <ChatView/>;
            case 'files':
                return <FileManager/>;
            case 'tasks':
                return <TaskManager/>;
            case 'settings':
                return <SettingsView user={user}/>;
            default:
                return <ChatView/>;
        }
    };

    return (
        <div className="flex h-screen bg-zinc-50 dark:bg-zinc-950 overflow-hidden font-sans">
            <Sidebar activeTab={activeTab} onTabChange={setActiveTab} user={user} />

            <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <header
                    className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 h-16 flex items-center px-8 justify-between shrink-0">
                    <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 capitalize">
                        {activeTab === 'chat' ? 'Chat Assistant' :
                            activeTab === 'files' ? 'File Manager' :
                                activeTab === 'tasks' ? 'Recursive Tasks' : 'Settings'}
                    </h1>
                </header>

                <div className="flex-1 overflow-auto p-8">
                    <div className="max-w-6xl mx-auto h-full">
                        {renderContent()}
                    </div>
                </div>
            </main>
        </div>
    );
}

export default Dashboard;