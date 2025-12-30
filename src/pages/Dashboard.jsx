import {useState, useEffect} from 'react';
import {getCurrentUser} from '../lib/supabase';
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
            try {
                const user = await getCurrentUser();
                setUser(user);
            } catch (error) {
                console.error("Error fetching user:", error);
            } finally {
                setLoading(false);
            }
        };
        getUser();
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
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
        <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden font-sans">
            <Sidebar activeTab={activeTab} onTabChange={setActiveTab} user={user} />

            <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <header
                    className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 h-16 flex items-center px-8 justify-between shrink-0">
                    <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100 capitalize">
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
