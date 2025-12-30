import {User, Mail, Shield, Bell, LogOut} from 'lucide-react';
import {supabase} from '../../lib/supabase';
import {useNavigate} from 'react-router-dom';

export default function SettingsView({user}) {
    const navigate = useNavigate();

    const handleSignOut = async () => {
        await supabase.auth.signOut();
        navigate('/login');
    };

    return (
        <div className="max-w-2xl space-y-8">
            <div>
                <h2 className="text-2xl font-bold text-white mb-6">Account Settings</h2>

                <div
                    className="bg-secondary-dark-bg rounded-lg shadow-sm border border-dark-border divide-y dark:divide-dark-border">
                    <div className="p-6">
                        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                            <User size={20}/> Profile Information
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label
                                    className="block text-sm font-medium text-gray-200 mb-1">Email</label>
                                <div
                                    className="flex items-center gap-2 text-dark-input-placeholder bg-dark-input-bg px-3 py-2 rounded-md border border-dark-input-border">
                                    <Mail size={16} className="text-zinc-400"/>
                                    {user?.email || 'user@example.com'}
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-200 mb-1">Full
                                    Name</label>
                                <input
                                    type="text"
                                    defaultValue={user?.user_metadata?.full_name || ''}
                                    placeholder="Your Name"
                                    className="rounded-lg  block w-full px-3 py-2 bg-dark-input-bg border-gray-600 placeholder-dark-input-placeholder text-white transition-shadow"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="p-6">
                        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                            <Bell size={20}/> Preferences
                        </h3>

                        <div className="space-y-4">
                            <label className="flex items-center gap-3 cursor-pointer">
                                <input type="checkbox" className="w-4 h-4 text-blue-500 rounded focus:ring-blue-400"
                                       defaultChecked/>
                                <span className="text-gray-200">Email Notifications for task completions</span>
                            </label>
                            <label className="flex items-center gap-3 cursor-pointer">
                                <input type="checkbox" className="w-4 h-4 text-blue-500 rounded focus:ring-blue-400"/>
                                <span className="text-gray-200">Dark Mode (System Default)</span>
                            </label>
                        </div>
                    </div>

                    <div className="p-6">
                        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                            <Shield size={20}/> Security
                        </h3>
                        <a href='/update-password' className="text-blue-500 hover:underline text-sm font-medium">Change
                            Password</a>
                    </div>

                    <div className="p-6">
                        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                            <LogOut size={20} className="text-red-400"/> Danger Zone
                        </h3>
                        <button
                            onClick={handleSignOut}
                            className="px-4 py-2 border border-red-700/50 text-red-300 rounded-md hover:bg-red-800/90 transition-colors text-sm font-medium"
                        >
                            Sign Out
                        </button>
                    </div>
                </div>
            </div>

            <div className="flex justify-end gap-3 py-4">
                <button
                    className="px-4 py-2 text-gray-300 hover:text-white hover:cursor-pointer">Cancel
                </button>
                <button
                    className="px-4 py-2 bg-primary-dark-btn text-white rounded-md hover:bg-primary-dark-btn-hover shadow-sm transition-colors">Save
                    Changes
                </button>
            </div>
        </div>
    );
}