import {useState, useEffect} from 'react';
import {Clock, Play, Pause, MoreVertical, Plus, X, Trash, Edit} from 'lucide-react';
import {Toaster} from 'react-hot-toast';
import {useAuth} from '../../hooks/useAuth';
import AutoReplySection from './AutoReplySection';

export default function TaskManager() {
    const { session, googleIntegration } = useAuth();
    const gmailConnected = googleIntegration.scopes?.includes('https://mail.google.com/');
    const [tasks, setTasks] = useState([
        {
            id: 1,
            name: 'Daily News Summary',
            schedule: 'Every day at 9:00 AM',
            status: 'active',
            lastRun: 'Today, 9:00 AM'
        },
        {id: 2, name: 'Inbox Cleanup', schedule: 'Every Friday at 5:00 PM', status: 'paused', lastRun: 'Last Friday'},
    ]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [activeMenuId, setActiveMenuId] = useState(null);

    // New Task Form State
    const [newTaskName, setNewTaskName] = useState('');
    const [newTaskSchedule, setNewTaskSchedule] = useState('');

    const toggleStatus = (id) => {
        setTasks(tasks.map(t =>
            t.id === id ? {...t, status: t.status === 'active' ? 'paused' : 'active'} : t
        ));
    };

    const handleAddTask = (e) => {
        e.preventDefault();
        if (!newTaskName || !newTaskSchedule) return;

        const newTask = {
            id: Date.now(),
            name: newTaskName,
            schedule: newTaskSchedule,
            status: 'active',
            lastRun: 'Never'
        };

        setTasks([...tasks, newTask]);
        setIsModalOpen(false);
        setNewTaskName('');
        setNewTaskSchedule('');
    };

    const handleDeleteTask = (id) => {
        setTasks(tasks.filter(t => t.id !== id));
        setActiveMenuId(null);
    };

    // Click outside to close menu
    useEffect(() => {
        const handleClickOutside = () => setActiveMenuId(null);
        if (activeMenuId) {
            document.addEventListener('click', handleClickOutside);
        }
        return () => document.removeEventListener('click', handleClickOutside);
    }, [activeMenuId]);


    return (
        <div className="space-y-6 relative">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-white">Recursive Tasks</h2>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                    <Plus size={18}/>
                    <span>New Task</span>
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tasks.map((task) => (
                    <div key={task.id}
                         className="bg-secondary-dark-bg p-6 rounded-lg shadow-sm border border-dark-border flex flex-col justify-between relative">
                        <div className="flex justify-between items-start mb-4">
                            <div
                                className={`p-2 rounded-lg ${task.status === 'active' ? 'bg-green-800/30 text-green-400' : 'bg-gray-700 text-zinc-300'}`}>
                                <Clock size={24}/>
                            </div>
                            <div className="relative" onClick={e => e.stopPropagation()}>
                                <button
                                    onClick={() => setActiveMenuId(activeMenuId === task.id ? null : task.id)}
                                    className="text-gray-300 hover:text-gray-100 p-1 rounded-md hover:bg-gray-700 transition-colors"
                                >
                                    <MoreVertical size={20}/>
                                </button>
                                {activeMenuId === task.id && (
                                    <div
                                        className="absolute right-0 mt-2 w-32 bg-gray-700 rounded-md shadow-lg ring-1 ring-gray-600 ring-opacity-5 z-10 border border-gray-600 py-1">
                                        <button
                                            className="w-full text-left px-4 py-2 text-sm text-gray-100 hover:bg-gray-600 flex items-center gap-2"
                                            onClick={() => {
                                                // Add edit logic here if needed
                                                setActiveMenuId(null);
                                            }}
                                        >
                                            <Edit size={14}/> Edit
                                        </button>
                                        <button
                                            onClick={() => handleDeleteTask(task.id)}
                                            className="w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-red-800/20 flex items-center gap-2"
                                        >
                                            <Trash size={14}/> Delete
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="mb-4">
                            <h3 className="font-semibold text-lg text-white mb-1">{task.name}</h3>
                            <p className="text-sm text-gray-300">{task.schedule}</p>
                        </div>

                        <div
                            className="flex items-center justify-between mt-auto pt-4 border-t border-dark-border">
                            <span className="text-xs text-gray-400">Last run: {task.lastRun}</span>
                            <button
                                onClick={() => toggleStatus(task.id)}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                                    task.status === 'active'
                                        ? 'hover:bg-amber-800/50 bg-amber-800/30 text-amber-400'
                                        : 'hover:bg-green-800 bg-green-800/30 text-green-400'
                                }`}
                            >
                                {task.status === 'active' ? (
                                    <>
                                        <Pause size={12} fill="currentColor"/> Pause
                                    </>
                                ) : (
                                    <>
                                        <Play size={12} fill="currentColor"/> Resume
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* New Task Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div
                        className="bg-secondary-dark-bg rounded-lg shadow-xl max-w-md w-full overflow-hidden border border-dark-border">
                        <div
                            className="flex justify-between items-center p-4 border-b border-dark-border">
                            <h3 className="text-lg font-semibold text-white">Create New Task</h3>
                            <button onClick={() => setIsModalOpen(false)}
                                    className="text-gray-400 hover:text-gray-200">
                                <X size={20}/>
                            </button>
                        </div>
                        <form onSubmit={handleAddTask} className="p-4 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-200 mb-1">Task Name</label>
                                <input
                                    type="text"
                                    value={newTaskName}
                                    onChange={(e) => setNewTaskName(e.target.value)}
                                    placeholder="e.g., Daily Summary"
                                    className="w-full bg-dark-input-bg border border-dark-input-border placeholder-dark-input-placeholder rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none text-white"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-200 mb-1">Schedule</label>
                                <input
                                    type="text"
                                    value={newTaskSchedule}
                                    onChange={(e) => setNewTaskSchedule(e.target.value)}
                                    placeholder="e.g., Every day at 9am"
                                    className="w-full bg-dark-input-bg border border-dark-input-border placeholder-dark-input-placeholder rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none text-white"
                                    required
                                />
                            </div>
                            <div className="flex justify-end gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="px-4 py-2 text-gray-300 hover:text-gray-100"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-primary-dark-btn text-white rounded-md hover:bg-primary-dark-btn-hover shadow-sm transition-colors"
                                >
                                    Create Task
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Auto-Reply Rules */}
            {session && gmailConnected && (
                <div className="bg-secondary-dark-bg rounded-lg shadow-sm border border-dark-border">
                    <Toaster />
                    <AutoReplySection session={session} />
                </div>
            )}
        </div>
    );
}