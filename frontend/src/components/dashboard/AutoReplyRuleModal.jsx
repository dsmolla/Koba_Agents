import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const TONES = ['Professional', 'Casual', 'Brief'];

export default function AutoReplyRuleModal({ isOpen, onClose, onSave, rule }) {
    const [formData, setFormData] = useState({
        name: '',
        when_condition: '',
        do_action: '',
        tone: 'Professional',
    });
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (rule) {
            setFormData({
                name: rule.name || '',
                when_condition: rule.when_condition || '',
                do_action: rule.do_action || '',
                tone: rule.tone || 'Professional',
            });
        } else {
            setFormData({
                name: '',
                when_condition: '',
                do_action: '',
                tone: 'Professional',
            });
        }
    }, [rule, isOpen]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.name.trim() || !formData.when_condition.trim() || !formData.do_action.trim()) return;

        setSaving(true);
        try {
            await onSave({
                name: formData.name.trim(),
                when_condition: formData.when_condition.trim(),
                do_action: formData.do_action.trim(),
                tone: formData.tone,
            });
        } finally {
            setSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <div className="bg-secondary-dark-bg border border-dark-border rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between p-4 border-b border-dark-border">
                    <h3 className="text-lg font-medium text-white">
                        {rule ? 'Edit Rule' : 'Create Auto-Reply Rule'}
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-4 space-y-4">
                    {/* Rule Name */}
                    <div>
                        <label className="block text-sm font-medium text-gray-200 mb-1">Rule Name</label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            placeholder="e.g., Decline recruiter emails"
                            required
                            className="w-full bg-dark-input-bg border border-gray-600 text-white rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                        />
                    </div>

                    {/* When */}
                    <div>
                        <label className="block text-sm font-medium text-gray-200 mb-1">
                            When
                        </label>
                        <textarea
                            name="when_condition"
                            value={formData.when_condition}
                            onChange={handleChange}
                            placeholder="e.g., Sender is a recruiter or mentions job offers, interviews, or hiring"
                            required
                            rows={3}
                            className="w-full bg-dark-input-bg border border-gray-600 text-white rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none resize-vertical"
                        />
                        <p className="text-xs text-gray-500 mt-1">Describe when this rule should apply.</p>
                    </div>

                    {/* Do */}
                    <div>
                        <label className="block text-sm font-medium text-gray-200 mb-1">
                            Do
                        </label>
                        <textarea
                            name="do_action"
                            value={formData.do_action}
                            onChange={handleChange}
                            placeholder="e.g., Draft a polite decline explaining I'm not looking for new opportunities"
                            required
                            rows={3}
                            className="w-full bg-dark-input-bg border border-gray-600 text-white rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none resize-vertical"
                        />
                        <p className="text-xs text-gray-500 mt-1">What the AI should do. Can be a reply, Drive action, Calendar check, etc.</p>
                    </div>

                    {/* Tone */}
                    <div>
                        <label className="block text-sm font-medium text-gray-200 mb-2">Tone</label>
                        <div className="flex gap-2">
                            {TONES.map(t => (
                                <button
                                    key={t}
                                    type="button"
                                    onClick={() => setFormData(prev => ({ ...prev, tone: t }))}
                                    className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                                        formData.tone === t
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-dark-input-bg border border-gray-600 text-gray-300 hover:border-gray-400'
                                    }`}
                                >
                                    {t}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex justify-end gap-2 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-300 hover:text-white transition-colors text-sm"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={saving || !formData.name.trim() || !formData.when_condition.trim() || !formData.do_action.trim()}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                        >
                            {saving ? 'Saving...' : (rule ? 'Update Rule' : 'Create Rule')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
