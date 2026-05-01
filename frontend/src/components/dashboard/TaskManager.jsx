import { useState, useEffect } from 'react';
import { Clock, Play, Pause, MoreVertical, Plus, X, Trash, Activity, Edit2, FileIcon, FileText, FileSpreadsheet } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import { useAuth, useGoogleIntegration } from '../../hooks/useAuth';
import AutoReplySection from './AutoReplySection';
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function TaskManager() {
    const { session } = useAuth();
    const { googleIntegration } = useGoogleIntegration();
    const gmailConnected = googleIntegration.scopes?.includes('https://mail.google.com/');

    const [tasks, setTasks] = useState([]);
    const [loadingTasks, setLoadingTasks] = useState(true);
    const [expandedLogs, setExpandedLogs] = useState({}); // task_id -> logs array

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [activeMenuId, setActiveMenuId] = useState(null);
    const [editingTask, setEditingTask] = useState(null);
    const [selectedLog, setSelectedLog] = useState(null);
    const [logHistory, setLogHistory] = useState([]);
    const [logHistoryLoading, setLogHistoryLoading] = useState(false);

    // New Task Form State
    const [newTaskName, setNewTaskName] = useState('');
    const [newTaskPrompt, setNewTaskPrompt] = useState('');

    // Frequency UI State
    const [frequency, setFrequency] = useState('daily');
    const [timeField, setTimeField] = useState('09:00');
    const [hourInterval, setHourInterval] = useState('1');
    const [selectedDays, setSelectedDays] = useState(['1']);

    const parseCronToUI = (cron) => {
        const parts = cron.split(' ');
        if (parts.length !== 5) return { frequency: 'daily', timeField: '09:00', hourInterval: '1', selectedDays: ['1'] };

        const [min, hour, dayOfMonth, month, dayOfWeek] = parts;

        if (min === '0' && hour.startsWith('*/')) {
            return { frequency: 'hourly', hourInterval: hour.replace('*/', ''), timeField: '09:00', selectedDays: ['1'] };
        }

        const parsedMin = min.padStart(2, '0');
        const parsedHour = hour.padStart(2, '0');

        if (dayOfWeek !== '*' && dayOfWeek !== '?') {
            return { frequency: 'weekly', timeField: `${parsedHour}:${parsedMin}`, selectedDays: dayOfWeek.split(','), hourInterval: '1' };
        }

        return { frequency: 'daily', timeField: `${parsedHour}:${parsedMin}`, selectedDays: ['1'], hourInterval: '1' };
    };

    const handleNewTaskClick = () => {
        setEditingTask(null);
        setNewTaskName('');
        setFrequency('daily');
        setTimeField('09:00');
        setNewTaskPrompt('');
        setIsModalOpen(true);
    };

    const handleEditTaskClick = (task) => {
        setEditingTask(task);
        setNewTaskName(task.name);
        setNewTaskPrompt(task.prompt);

        const uiState = parseCronToUI(task.cron_schedule);
        setFrequency(uiState.frequency);
        setTimeField(uiState.timeField);
        setHourInterval(uiState.hourInterval);
        setSelectedDays(uiState.selectedDays);

        setIsModalOpen(true);
        setActiveMenuId(null);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setEditingTask(null);
        setNewTaskName('');
        setFrequency('daily');
        setTimeField('09:00');
        setNewTaskPrompt('');
    };

    const getFileIcon = (mimeType, size = 24) => {
        if (!mimeType) return <FileIcon size={size} className="text-gray-400" />;
        if (mimeType.includes('spreadsheet') || mimeType.includes('csv')) {
            return <FileSpreadsheet size={size} className="text-green-400" />;
        }
        if (mimeType.includes('document') || mimeType.includes('word') || mimeType.includes('pdf')) {
            return <FileText size={size} className="text-blue-400" />;
        }
        return <FileIcon size={size} className="text-gray-400" />;
    };

    const downloadFile = async (file) => {
        try {
            const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/drive/download/${file.id}`, {
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });
            if (!res.ok) throw new Error("Failed to download");
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.filename || "download";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (e) {
            console.error("Error downloading file", e);
            alert("Failed to download file");
        }
    };

    const handleLogClick = async (log) => {
        setSelectedLog(log);
        if (!log.thread_id) {
            setLogHistory([{ sender: 'bot', content: log.output }]);
            return;
        }

        setLogHistoryLoading(true);
        try {
            const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/tasks/${log.thread_id}`, {
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setLogHistory(data.messages || []);
            } else {
                setLogHistory([{ sender: 'bot', content: 'Failed to load execution history.' }]);
            }
        } catch (e) {
            console.error(e);
            setLogHistory([{ sender: 'bot', content: 'Failed to load execution history.' }]);
        } finally {
            setLogHistoryLoading(false);
        }
    };

    const fetchTasks = async () => {
        try {
            const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/tasks`, {
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setTasks(data);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoadingTasks(false);
        }
    };

    const fetchLogs = async (taskId) => {
        if (expandedLogs[taskId]) {
            // Toggle off
            setExpandedLogs(prev => { const n = { ...prev }; delete n[taskId]; return n; });
            return;
        }
        try {
            const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/tasks/${taskId}/logs`, {
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setExpandedLogs(prev => ({ ...prev, [taskId]: data }));
            }
        } catch (e) {
            console.error("Failed to load logs", e);
        }
    };

    useEffect(() => {
        if (session?.access_token) {
            fetchTasks();
        }
    }, [session]);

    const toggleStatus = async (id, currentStatus) => {
        const newStatus = currentStatus === 'active' ? 'paused' : 'active';
        // Optimistic update
        setTasks(tasks.map(t => t.id === id ? { ...t, status: newStatus } : t));

        try {
            const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
            await fetch(`${apiUrl}/tasks/${id}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${session.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: newStatus })
            });
            fetchTasks();
        } catch (e) {
            console.error(e);
        }
    };

    const handleRunNow = async (id) => {
        try {
            const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/tasks/${id}/run`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session.access_token}`
                }
            });
            if (res.ok) {
                toast.success('Task execution triggered in the background');
            } else {
                toast.error('Failed to trigger task execution');
            }
        } catch (e) {
            console.error("Failed to run task", e);
            toast.error('Error triggering task execution');
        }
    };

    const handleAddTask = async (e) => {
        e.preventDefault();
        if (!newTaskName || !newTaskPrompt) return;

        let cron_schedule = '* * * * *';
        let human_schedule = '';
        const timeArr = timeField ? timeField.split(':') : ['09', '00'];
        const hours = parseInt(timeArr[0] || '9');
        const minutes = parseInt(timeArr[1] || '0');

        const ampm = hours >= 12 ? 'PM' : 'AM';
        const formattedHours = hours % 12 || 12;
        const formattedTime = `${formattedHours}:${minutes.toString().padStart(2, '0')} ${ampm}`;

        if (frequency === 'hourly') {
            const hInt = parseInt(hourInterval) || 1;
            cron_schedule = `0 */${hInt} * * *`;
            human_schedule = hInt === 1 ? `Every hour` : `Every ${hInt} hours`;
        } else if (frequency === 'daily') {
            cron_schedule = `${minutes} ${hours} * * *`;
            human_schedule = `Every day at ${formattedTime}`;
        } else if (frequency === 'weekly') {
            const daysCron = selectedDays.length > 0 ? selectedDays.join(',') : '*';
            cron_schedule = `${minutes} ${hours} * * ${daysCron}`;
            const daysNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
            const selectedNames = selectedDays.map(d => daysNames[d]).join(', ');
            human_schedule = `Every ${selectedNames} at ${formattedTime}`;
        }

        try {
            const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
            const method = editingTask ? 'PATCH' : 'POST';
            const url = editingTask ? `${apiUrl}/tasks/${editingTask.id}` : `${apiUrl}/tasks`;

            const res = await fetch(url, {
                method: method,
                headers: {
                    'Authorization': `Bearer ${session.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: newTaskName,
                    cron_schedule: cron_schedule,
                    human_schedule: human_schedule,
                    prompt: newTaskPrompt
                })
            });
            if (res.ok) {
                await fetchTasks();
                closeModal();
            } else {
                alert(`Failed to ${editingTask ? 'update' : 'create'} task`);
            }
        } catch (e) {
            console.error(e);
            alert(`Error ${editingTask ? 'updating' : 'creating'} task`);
        }
    };

    const handleDeleteTask = async (id) => {
        if (!confirm("Are you sure you want to delete this recursive task?")) return;
        setTasks(tasks.filter(t => t.id !== id));
        setActiveMenuId(null);
        try {
            const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
            await fetch(`${apiUrl}/tasks/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });
        } catch (e) { console.error(e); }
    };

    useEffect(() => {
        const handleClickOutside = () => setActiveMenuId(null);
        if (activeMenuId) document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    }, [activeMenuId]);

    return (
        <div className="space-y-6 relative pb-12">
            <div className="flex justify-between items-center bg-secondary-dark-bg p-6 rounded-lg shadow-sm border border-dark-border">
                <div>
                    <h2 className="text-2xl font-bold text-white mb-1">Recursive Tasks</h2>
                    <p className="text-sm text-gray-400">Manage scheduled background AI agents that run natively on a cron.</p>
                </div>
                <button
                    onClick={handleNewTaskClick}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors shadow-lg"
                >
                    <Plus size={18} />
                    <span>New Task</span>
                </button>
            </div>

            {loadingTasks ? (
                <div className="text-center py-12 text-gray-400 animate-pulse">Loading Tasks...</div>
            ) : tasks.length === 0 ? (
                <div className="text-center py-12 border border-dashed border-dark-border rounded-lg bg-secondary-dark-bg/50">
                    <p className="text-gray-400 mb-2">No recursive tasks scheduled.</p>
                    <p className="text-xs text-gray-500">Ask the Koba Agent to "Schedule a daily summary" or create one manually!</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                    {tasks.map((task) => (
                        <div key={task.id} className="bg-secondary-dark-bg rounded-lg shadow-sm border border-dark-border flex flex-col relative overflow-hidden transition-all duration-300">
                            <div className="p-6">
                                <div className="flex justify-between items-start mb-4">
                                    <div className={`p-2 rounded-lg ${task.status === 'active' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-primary-dark-bg text-zinc-500 border border-dark-border'}`}>
                                        <Clock size={20} />
                                    </div>
                                    <div className="relative" onClick={e => e.stopPropagation()}>
                                        <button
                                            onClick={() => setActiveMenuId(activeMenuId === task.id ? null : task.id)}
                                            className="text-gray-400 hover:text-white p-1 rounded-md transition-colors"
                                        >
                                            <MoreVertical size={20} />
                                        </button>
                                        {activeMenuId === task.id && (
                                            <div className="absolute right-0 mt-2 w-32 bg-dark-input-bg rounded-md shadow-2xl ring-1 ring-dark-border z-20 border border-dark-border py-1">
                                                <button
                                                    onClick={() => handleEditTaskClick(task)}
                                                    className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-white/5 flex items-center gap-2 border-b border-dark-border"
                                                >
                                                    <Edit2 size={14} /> Edit
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteTask(task.id)}
                                                    className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-2"
                                                >
                                                    <Trash size={14} /> Delete
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="mb-4">
                                    <h3 className="font-semibold text-lg text-white mb-1">{task.name}</h3>
                                    <p className="text-xs text-primary-400 font-mono mb-2">{task.human_schedule}</p>
                                    <p className="text-sm text-gray-400 bg-primary-dark-bg p-3 rounded-md italic">"{task.prompt}"</p>
                                </div>

                                <div className="flex items-center justify-between pt-4 mt-auto">
                                    <button
                                        onClick={() => fetchLogs(task.id)}
                                        className="text-xs flex items-center gap-1.5 text-gray-400 hover:text-white transition-colors">
                                        <Activity size={14} /> View Logs
                                    </button>
                                    <button
                                        onClick={() => handleRunNow(task.id)}
                                        className="text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-full font-medium transition-colors hover:bg-blue-500/20 bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                        <Play size={12} fill="currentColor" /> Run Now
                                    </button>
                                    <button
                                        onClick={() => toggleStatus(task.id, task.status)}
                                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${task.status === 'active'
                                            ? 'hover:bg-amber-500/20 bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                            : 'hover:bg-green-500/20 bg-green-500/10 text-green-400 border border-green-500/20'
                                            }`}
                                    >
                                        {task.status === 'active' ? (
                                            <><Pause size={12} fill="currentColor" /> Pause</>
                                        ) : (
                                            <><Play size={12} fill="currentColor" /> Resume</>
                                        )}
                                    </button>
                                </div>
                            </div>

                            {/* Expanded Logs Section */}
                            {expandedLogs[task.id] && (
                                <div className="bg-dark-input-bg p-4 border-t border-dark-border max-h-64 overflow-y-auto">
                                    <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-3">Execution History</h4>
                                    {expandedLogs[task.id].length === 0 ? (
                                        <p className="text-xs text-gray-500 italic">No logs generated yet.</p>
                                    ) : (
                                        <div className="space-y-3">
                                            {expandedLogs[task.id].map(log => (
                                                <div key={log.id} className="text-sm border-l-2 border-primary-500 pl-3">
                                                    <div className="flex justify-between items-center mb-1">
                                                        <span className="text-xs text-gray-400">{new Date(log.executed_at).toLocaleString()}</span>
                                                        <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${log.status === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>{log.status}</span>
                                                    </div>
                                                    <div
                                                        onClick={() => handleLogClick(log)}
                                                        className="text-gray-300 text-xs whitespace-pre-wrap cursor-pointer hover:text-white bg-black/10 p-2 rounded-md border border-white/5 transition-colors line-clamp-1"
                                                    >
                                                        {log.output && log.output.length > 150 ? log.output.substring(0, 150) + '...' : (log.output || 'No output')}
                                                    </div>
                                                    <p onClick={() => handleLogClick(log)} className="text-primary-400 text-[10px] mt-1 italic cursor-pointer">Click to view full output</p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* New Task Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
                    <div className="bg-secondary-dark-bg rounded-lg shadow-2xl max-w-lg w-full overflow-hidden border border-dark-border">
                        <div className="flex justify-between items-center p-5 border-b border-dark-border bg-primary-950/60">
                            <h3 className="text-lg font-semibold text-white">{editingTask ? 'Edit Task' : 'Manually Create Task'}</h3>
                            <button onClick={closeModal} className="text-gray-400 hover:text-white transition-colors"><X size={20} /></button>
                        </div>
                        <form onSubmit={handleAddTask} className="p-5 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Task Name</label>
                                <input type="text" value={newTaskName} onChange={(e) => setNewTaskName(e.target.value)} placeholder="Daily Summary" className="w-full bg-dark-input-bg border border-dark-border rounded-md px-3 py-2 outline-none text-white focus:border-primary-500" required />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Frequency</label>
                                    <select value={frequency} onChange={(e) => setFrequency(e.target.value)} className="w-full bg-dark-input-bg border border-dark-border rounded-md px-3 py-2 outline-none text-white focus:border-primary-500">
                                        <option value="hourly">Hourly</option>
                                        <option value="daily">Daily</option>
                                        <option value="weekly">Weekly</option>
                                    </select>
                                </div>
                                {frequency === 'hourly' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-1">Every X Hours</label>
                                        <input type="number" min="1" max="23" value={hourInterval} onChange={(e) => setHourInterval(e.target.value)} className="w-full bg-dark-input-bg border border-dark-border rounded-md px-3 py-2 outline-none text-white focus:border-primary-500" />
                                    </div>
                                )}
                                {(frequency === 'daily' || frequency === 'weekly') && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-1">Time of Day</label>
                                        <input type="time" value={timeField} onChange={(e) => setTimeField(e.target.value)} className="w-full bg-dark-input-bg border border-dark-border rounded-md px-3 py-2 outline-none text-white focus:border-primary-500 [&::-webkit-calendar-picker-indicator]:filter [&::-webkit-calendar-picker-indicator]:invert" required />
                                    </div>
                                )}
                                {frequency === 'weekly' && (
                                    <div className="col-span-2">
                                        <label className="block text-sm font-medium text-gray-300 mb-2">Repeat On</label>
                                        <div className="flex flex-wrap gap-2">
                                            {[
                                                { value: '0', label: 'Sun' }, { value: '1', label: 'Mon' },
                                                { value: '2', label: 'Tue' }, { value: '3', label: 'Wed' },
                                                { value: '4', label: 'Thu' }, { value: '5', label: 'Fri' },
                                                { value: '6', label: 'Sat' }
                                            ].map(day => (
                                                <button
                                                    type="button"
                                                    key={day.value}
                                                    onClick={() => {
                                                        let newDays;
                                                        if (selectedDays.includes(day.value)) {
                                                            newDays = selectedDays.filter(d => d !== day.value);
                                                            if (newDays.length === 0) newDays = [day.value];
                                                        } else {
                                                            newDays = [...selectedDays, day.value];
                                                        }
                                                        setSelectedDays(newDays);
                                                    }}
                                                    className={`px-3 py-1.5 rounded-md text-sm transition-colors font-medium border ${selectedDays.includes(day.value) ? 'bg-primary-600 text-white border-primary-500 shadow-sm' : 'bg-dark-input-bg text-gray-400 hover:text-white hover:border-gray-500 border-dark-border'
                                                        }`}
                                                >
                                                    {day.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Agent Prompt</label>
                                <textarea value={newTaskPrompt} onChange={(e) => setNewTaskPrompt(e.target.value)} placeholder="Exactly what do you want the agent to do when it wakes up?" rows={3} className="w-full bg-dark-input-bg border border-dark-border rounded-md px-3 py-2 outline-none text-white focus:border-primary-500 resize-none" required />
                            </div>
                            <div className="flex justify-end gap-3 pt-4 border-t border-dark-border">
                                <button type="button" onClick={closeModal} className="px-4 py-2 text-gray-400 hover:text-white transition-colors">Cancel</button>
                                <button type="submit" className="px-5 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 shadow-md transition-colors font-medium">{editingTask ? 'Save Changes' : 'Deploy Task'}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Log Viewer Modal */}
            {selectedLog && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
                    <div className="bg-secondary-dark-bg w-full max-w-3xl max-h-[85vh] rounded-xl shadow-2xl flex flex-col border border-dark-border">
                        <div className="flex justify-between items-center p-5 border-b border-dark-border bg-primary-950/60 rounded-t-xl">
                            <div>
                                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                    <Activity size={18} className="text-primary-400" /> Execution Log
                                </h3>
                                <p className="text-xs text-gray-400 mt-0.5">{new Date(selectedLog.executed_at).toLocaleString()}</p>
                            </div>
                            <button onClick={() => setSelectedLog(null)} className="text-gray-400 hover:text-white transition-colors bg-black/20 p-1.5 rounded-md hover:bg-black/40"><X size={20} /></button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-6 bg-primary-dark-bg custom-scrollbar flex flex-col gap-6 rounded-b-xl">
                            {logHistoryLoading ? (
                                <div className="text-center py-12 text-gray-400 animate-pulse">Loading execution thread...</div>
                            ) : logHistory.length === 0 ? (
                                <div className="text-center py-12 text-gray-500 italic">No messages found in this execution thread.</div>
                            ) : (
                                logHistory.map((msg, idx) => (
                                    <div key={idx} className={`w-full max-w-xl ${msg.sender === 'user' ? 'self-end' : 'self-start'}`}>
                                        <div className={`p-4 rounded-xl min-w-0 shadow-lg ${msg.sender === 'user'
                                            ? 'bg-primary-600 text-white rounded-tr-none shadow-primary-500/20'
                                            : 'bg-primary-900/60 border border-primary-800/40 text-primary-50 rounded-tl-none backdrop-blur-sm'}`}>
                                            {msg.content && (
                                                <Markdown
                                                    remarkPlugins={[remarkGfm]}
                                                    components={{
                                                        p: ({ node, ...props }) => <p className="text-sm my-2 whitespace-pre-wrap leading-relaxed" {...props} />,
                                                        h1: ({ node, ...props }) => <h1 className="text-2xl font-bold my-4 border-b border-white/10 pb-2" {...props} />,
                                                        h2: ({ node, ...props }) => <h2 className="text-xl font-bold my-3 border-b border-white/10 pb-2" {...props} />,
                                                        h3: ({ node, ...props }) => <h3 className="text-lg font-bold my-2" {...props} />,
                                                        h4: ({ node, ...props }) => <h4 className="text-base font-bold my-2" {...props} />,
                                                        ul: ({ node, ...props }) => <ul className="list-disc pl-5 my-3 space-y-1 text-sm marker:text-primary-300/70" {...props} />,
                                                        ol: ({ node, ...props }) => <ol className="list-decimal pl-5 my-3 space-y-1 text-sm marker:text-primary-300/70" {...props} />,
                                                        li: ({ node, ...props }) => <li className="text-sm leading-relaxed" {...props} />,
                                                        a: ({ node, ...props }) => <a className="text-primary-300 hover:text-primary-200 underline underline-offset-2 transition-colors" target="_blank" rel="noopener noreferrer" {...props} />,
                                                        blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-primary-500/50 pl-4 py-1 my-3 bg-black/10 text-gray-300 italic rounded-r-lg" {...props} />,
                                                        table: ({ node, ...props }) => (
                                                            <div className="overflow-x-auto my-4 rounded-lg border border-white/10">
                                                                <table className="min-w-full divide-y divide-white/10 bg-black/10 text-sm" {...props} />
                                                            </div>
                                                        ),
                                                        thead: ({ node, ...props }) => <thead className="bg-black/30" {...props} />,
                                                        tbody: ({ node, ...props }) => <tbody className="divide-y divide-white/10" {...props} />,
                                                        tr: ({ node, ...props }) => <tr className="hover:bg-black/20 transition-colors" {...props} />,
                                                        th: ({ node, ...props }) => <th className="px-4 py-3 text-left font-semibold text-gray-100 uppercase tracking-wider text-xs" {...props} />,
                                                        td: ({ node, ...props }) => <td className="px-4 py-3 text-gray-200" {...props} />,
                                                        code({ node, inline, className, children, ...props }) {
                                                            const match = /language-(\w+)/.exec(className || '');
                                                            return !inline && match ? (
                                                                <div className="my-4 rounded-xl overflow-hidden shadow-lg border border-white/10">
                                                                    <div className="bg-secondary-dark-bg/90 px-4 py-2 text-xs text-dark-input-placeholder font-mono uppercase border-b border-white/10">
                                                                        {match[1]}
                                                                    </div>
                                                                    <SyntaxHighlighter
                                                                        style={vscDarkPlus}
                                                                        language={match[1]}
                                                                        PreTag="div"
                                                                        className="!m-0 !bg-primary-dark-bg/80 !p-4 !text-xs custom-scrollbar"
                                                                        customStyle={{ background: 'transparent' }}
                                                                        {...props}
                                                                    >
                                                                        {String(children).replace(/\n$/, '')}
                                                                    </SyntaxHighlighter>
                                                                </div>
                                                            ) : (
                                                                <code className="bg-black/40 px-1.5 py-0.5 rounded-md text-[0.85em] font-mono text-primary-200 border border-white/5" {...props}>
                                                                    {children}
                                                                </code>
                                                            );
                                                        }
                                                    }}
                                                >
                                                    {msg.content}
                                                </Markdown>
                                            )}

                                            {msg.files && msg.files.length > 0 && (
                                                <div className={`flex flex-col gap-2 ${msg.content ? 'mt-3 pt-3 border-t border-white/10' : ''}`}>
                                                    <p className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-1">Generated Files</p>
                                                    {msg.files.map((file, fidx) => (
                                                        <div key={file?.id || fidx} className="flex items-center gap-3 bg-black/20 p-2.5 rounded-lg cursor-pointer hover:bg-black/40 border border-white/5 transition-colors" onClick={() => downloadFile(file)}>
                                                            <div className="p-2 bg-white/10 rounded-lg shrink-0">
                                                                {getFileIcon(file.mime_type?.split('/')[0], 20)}
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <p className="text-sm font-medium truncate text-gray-200">{file.filename}</p>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Auto-Reply Rules */}
            {session && gmailConnected && (
                <div className="bg-secondary-dark-bg rounded-lg shadow-sm border border-dark-border mt-12 mb-12">
                    <Toaster />
                    <AutoReplySection session={session} />
                </div>
            )}
        </div>
    );
}