import { useState, useEffect, useCallback } from 'react';
import { MailPlus, Plus, Trash2, Edit2, ChevronDown, ChevronUp, GripVertical, Radio, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import {
    DndContext,
    closestCenter,
    PointerSensor,
    useSensor,
    useSensors,
} from '@dnd-kit/core';
import {
    SortableContext,
    verticalListSortingStrategy,
    useSortable,
    arrayMove,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import AutoReplyRuleModal from './AutoReplyRuleModal';

const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

function SortableRuleItem({ rule, onToggle, onEdit, onDelete }) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: rule.id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`p-3 rounded-lg border transition-colors ${
                rule.is_enabled
                    ? 'bg-dark-input-bg/30 border-dark-border'
                    : 'bg-dark-input-bg/10 border-dark-border/50 opacity-60'
            }`}
        >
            <div className="flex items-start gap-3">
                <button
                    {...attributes}
                    {...listeners}
                    className="mt-0.5 flex-shrink-0 text-gray-600 hover:text-gray-400 cursor-grab active:cursor-grabbing transition-colors"
                    title="Drag to reorder"
                    tabIndex={-1}
                >
                    <GripVertical size={16} />
                </button>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-gray-200 font-medium text-sm truncate">{rule.name}</h4>
                        <span className={`text-xs px-1.5 py-0.5 rounded flex-shrink-0 ${
                            rule.is_enabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
                        }`}>
                            {rule.is_enabled ? 'Active' : 'Disabled'}
                        </span>
                        <span className="text-xs px-1.5 py-0.5 rounded bg-dark-input-bg border border-dark-border text-gray-500 flex-shrink-0">
                            {rule.tone}
                        </span>
                    </div>
                    <p className="text-xs text-gray-500 truncate">
                        <span className="text-gray-400">When</span> {rule.when_condition}
                    </p>
                    <p className="text-xs text-gray-500 truncate mt-0.5">
                        <span className="text-gray-400">Do</span> {rule.do_action}
                    </p>
                </div>

                <div className="flex items-center gap-1 flex-shrink-0">
                    <button
                        onClick={() => onToggle(rule.id)}
                        className={`relative w-9 h-5 rounded-full transition-colors ${
                            rule.is_enabled ? 'bg-blue-600' : 'bg-gray-600'
                        }`}
                        title={rule.is_enabled ? 'Disable' : 'Enable'}
                    >
                        <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                            rule.is_enabled ? 'translate-x-4' : 'translate-x-0'
                        }`} />
                    </button>
                    <button
                        onClick={() => onEdit(rule)}
                        className="p-1.5 text-gray-400 hover:text-blue-400 transition-colors"
                        title="Edit"
                    >
                        <Edit2 size={14} />
                    </button>
                    <button
                        onClick={() => onDelete(rule.id)}
                        className="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
                        title="Delete"
                    >
                        <Trash2 size={14} />
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function AutoReplySection({ session }) {
    const [rules, setRules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [watchActive, setWatchActive] = useState(false);
    const [watchToggling, setWatchToggling] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [editingRule, setEditingRule] = useState(null);
    const [showLog, setShowLog] = useState(false);
    const [logEntries, setLogEntries] = useState([]);
    const [logLoading, setLogLoading] = useState(false);

    const headers = { 'Authorization': `Bearer ${session.access_token}` };

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: { distance: 5 },
        })
    );

    const fetchRules = useCallback(async () => {
        try {
            const response = await fetch(`${apiUrl}/auto-reply/rules`, { headers });
            if (response.ok) setRules(await response.json());
        } catch (error) {
            console.error('Failed to fetch rules:', error);
        } finally {
            setLoading(false);
        }
    }, [session.access_token]);

    const fetchWatchStatus = useCallback(async () => {
        try {
            const response = await fetch(`${apiUrl}/auto-reply/watch`, { headers });
            if (response.ok) {
                const data = await response.json();
                setWatchActive(data.is_active);
            }
        } catch (error) {
            console.error('Failed to fetch watch status:', error);
        }
    }, [session.access_token]);

    useEffect(() => {
        fetchRules();
        fetchWatchStatus();
    }, [fetchRules, fetchWatchStatus]);

    const handleToggleWatch = async () => {
        setWatchToggling(true);
        try {
            const response = await fetch(`${apiUrl}/auto-reply/watch/toggle`, {
                method: 'POST',
                headers,
            });
            if (response.ok) {
                const data = await response.json();
                setWatchActive(data.is_active);
                toast.success(data.is_active ? 'Watch started' : 'Watch stopped');
            } else {
                toast.error('Failed to toggle watch');
            }
        } catch {
            toast.error('Failed to toggle watch');
        } finally {
            setWatchToggling(false);
        }
    };

    const handleSaveRule = async (payload) => {
        try {
            const isEdit = !!editingRule;
            const url = isEdit
                ? `${apiUrl}/auto-reply/rules/${editingRule.id}`
                : `${apiUrl}/auto-reply/rules`;

            const response = await fetch(url, {
                method: isEdit ? 'PUT' : 'POST',
                headers: { ...headers, 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                toast.success(isEdit ? 'Rule updated' : 'Rule created');
                setModalOpen(false);
                setEditingRule(null);
                fetchRules();
            } else {
                const data = await response.json();
                toast.error(data.detail || 'Failed to save rule');
            }
        } catch {
            toast.error('Failed to save rule');
        }
    };

    const handleDeleteRule = async (ruleId) => {
        try {
            const response = await fetch(`${apiUrl}/auto-reply/rules/${ruleId}`, {
                method: 'DELETE',
                headers,
            });
            if (response.ok) {
                toast.success('Rule deleted');
                fetchRules();
            } else {
                toast.error('Failed to delete rule');
            }
        } catch {
            toast.error('Failed to delete rule');
        }
    };

    const handleToggleRule = async (ruleId) => {
        try {
            const response = await fetch(`${apiUrl}/auto-reply/rules/${ruleId}/toggle`, {
                method: 'PATCH',
                headers,
            });
            if (response.ok) {
                fetchRules();
            } else {
                toast.error('Failed to toggle rule');
            }
        } catch {
            toast.error('Failed to toggle rule');
        }
    };

    const handleReorder = useCallback(async (event) => {
        const { active, over } = event;
        if (!over || active.id === over.id) return;

        const oldIndex = rules.findIndex(r => r.id === active.id);
        const newIndex = rules.findIndex(r => r.id === over.id);
        const reordered = arrayMove(rules, oldIndex, newIndex);
        setRules(reordered);

        try {
            const response = await fetch(`${apiUrl}/auto-reply/rules/reorder`, {
                method: 'POST',
                headers: { ...headers, 'Content-Type': 'application/json' },
                body: JSON.stringify({ rule_ids: reordered.map(r => r.id) }),
            });
            if (!response.ok) {
                toast.error('Failed to save rule order');
                fetchRules();
            }
        } catch {
            toast.error('Failed to save rule order');
            fetchRules();
        }
    }, [rules, session.access_token, fetchRules]);

    const fetchLog = async () => {
        setLogLoading(true);
        try {
            const response = await fetch(`${apiUrl}/auto-reply/log`, { headers });
            if (response.ok) setLogEntries(await response.json());
        } catch (error) {
            console.error('Failed to fetch log:', error);
        } finally {
            setLogLoading(false);
        }
    };

    const handleToggleLog = () => {
        const newShowLog = !showLog;
        setShowLog(newShowLog);
        if (newShowLog) fetchLog();
    };

    if (loading) {
        return (
            <div className="p-6">
                <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                    <MailPlus size={20} /> Auto-Reply
                </h3>
                <p className="text-gray-400 text-sm">Loading...</p>
            </div>
        );
    }

    return (
        <div className="p-6">
            {/* Header */}
            <div className="flex justify-between items-center mb-2">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    <MailPlus size={20} /> Auto-Reply
                </h3>
                <div className="flex items-center gap-2">
                    {/* Watch toggle */}
                    <button
                        onClick={handleToggleWatch}
                        disabled={watchToggling}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors disabled:opacity-50 ${
                            watchActive
                                ? 'bg-green-600/20 text-green-400 hover:bg-green-600/30 border border-green-600/30'
                                : 'bg-dark-input-bg text-gray-400 hover:text-gray-200 border border-dark-border'
                        }`}
                        title={watchActive ? 'Stop watching inbox' : 'Start watching inbox'}
                    >
                        <Radio size={14} className={watchActive ? 'animate-pulse' : ''} />
                        {watchToggling ? '...' : watchActive ? 'Watching' : 'Watch Off'}
                    </button>
                    {/* Add rule */}
                    <button
                        onClick={() => { setEditingRule(null); setModalOpen(true); }}
                        className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-500 text-sm font-medium transition-colors"
                    >
                        <Plus size={16} /> Add Rule
                    </button>
                </div>
            </div>

            <p className="text-sm text-gray-400 mb-4">
                Rules are checked in priority order — the first matching rule runs. Drag to reorder.
            </p>

            {/* Rules List */}
            {rules.length === 0 ? (
                <div className="text-center py-8 text-gray-500 border border-dashed border-dark-border rounded-lg">
                    <MailPlus size={32} className="mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No auto-reply rules configured</p>
                    <p className="text-xs text-gray-600 mt-1">Create a rule to get started</p>
                </div>
            ) : (
                <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleReorder}
                >
                    <SortableContext
                        items={rules.map(r => r.id)}
                        strategy={verticalListSortingStrategy}
                    >
                        <div className="space-y-2">
                            {rules.map(rule => (
                                <SortableRuleItem
                                    key={rule.id}
                                    rule={rule}
                                    onToggle={handleToggleRule}
                                    onEdit={(rule) => { setEditingRule(rule); setModalOpen(true); }}
                                    onDelete={handleDeleteRule}
                                />
                            ))}
                        </div>
                    </SortableContext>
                </DndContext>
            )}

            {/* Activity Log */}
            {rules.length > 0 && (
                <div className="mt-4">
                    <button
                        onClick={handleToggleLog}
                        className="flex items-center gap-1 text-sm text-gray-400 hover:text-gray-200 transition-colors"
                    >
                        {showLog ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        Recent Activity
                    </button>

                    {showLog && (
                        <div className="mt-2 border border-dark-border rounded-lg overflow-hidden">
                            {logLoading ? (
                                <p className="text-xs text-gray-500 p-3">Loading...</p>
                            ) : logEntries.length === 0 ? (
                                <p className="text-xs text-gray-500 p-3">No auto-reply activity yet</p>
                            ) : (
                                <div className="max-h-48 overflow-y-auto">
                                    {logEntries.map(entry => (
                                        <div key={entry.id} className="flex items-center justify-between px-3 py-2 border-b border-dark-border/50 last:border-b-0">
                                            <div className="flex-1 min-w-0">
                                                <p className="text-xs text-gray-300 truncate">{entry.subject || '(no subject)'}</p>
                                                <p className="text-xs text-gray-500">{new Date(entry.replied_at).toLocaleString()}</p>
                                            </div>
                                            <div className="flex items-center gap-1 flex-shrink-0">
                                                <span className={`text-xs px-1.5 py-0.5 rounded ${
                                                    entry.status === 'sent' ? 'bg-green-500/20 text-green-400' :
                                                    entry.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                                    'bg-yellow-500/20 text-yellow-400'
                                                }`}>
                                                    {entry.status}
                                                </span>
                                                {entry.reply_message_id && entry.status === 'sent' && (
                                                    <a
                                                        href={`https://mail.google.com/mail/u/0/#sent/${entry.reply_message_id}`}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="p-1 text-gray-500 hover:text-blue-400 transition-colors"
                                                        title="View reply in Gmail"
                                                        onClick={e => e.stopPropagation()}
                                                    >
                                                        <ExternalLink size={12} />
                                                    </a>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Modal */}
            <AutoReplyRuleModal
                isOpen={modalOpen}
                onClose={() => { setModalOpen(false); setEditingRule(null); }}
                onSave={handleSaveRule}
                rule={editingRule}
            />
        </div>
    );
}
