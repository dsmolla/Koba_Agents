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
                <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-6">Account Settings</h2>

                <div
                    className="bg-white dark:bg-zinc-900 rounded-lg shadow-sm border border-zinc-200 dark:border-zinc-800 divide-y divide-zinc-200 dark:divide-zinc-800">
                    <div className="p-6">
                        <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-4 flex items-center gap-2">
                            <User size={20}/> Profile Information
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label
                                    className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Email</label>
                                <div
                                    className="flex items-center gap-2 text-zinc-900 dark:text-zinc-100 bg-zinc-50 dark:bg-zinc-800 px-3 py-2 rounded-md border border-zinc-200 dark:border-zinc-700">
                                    <Mail size={16} className="text-zinc-400"/>
                                    {user?.email || 'user@example.com'}
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Full
                                    Name</label>
                                <input
                                    type="text"
                                    defaultValue={user?.user_metadata?.full_name || ''}
                                    placeholder="Your Name"
                                    className="w-full bg-transparent border border-zinc-300 dark:border-zinc-700 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none transition-shadow"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="p-6">
                        <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-4 flex items-center gap-2">
                            <Bell size={20}/> Preferences
                        </h3>
                        <div className="space-y-4">
                            <label className="flex items-center gap-3 cursor-pointer">
                                <input type="checkbox" className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                                       defaultChecked/>
                                <span className="text-zinc-700 dark:text-zinc-300">Email Notifications for tasks</span>
                            </label>
                            <label className="flex items-center gap-3 cursor-pointer">
                                <input type="checkbox" className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"/>
                                <span className="text-zinc-700 dark:text-zinc-300">Dark Mode (System Default)</span>
                            </label>
                        </div>
                    </div>

                    <div className="p-6">
                        <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-4 flex items-center gap-2">
                            <Shield size={20}/> Security
                        </h3>
                        <a href='/update-password' className="text-blue-600 hover:underline text-sm font-medium">Change
                            Password</a>
                    </div>

                    <div className="p-6">
                        <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-4 flex items-center gap-2">
                            <LogOut size={20} className="text-red-500"/> Danger Zone
                        </h3>
                        <button
                            onClick={handleSignOut}
                            className="px-4 py-2 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-sm font-medium"
                        >
                            Sign Out
                        </button>
                    </div>
                </div>
            </div>

            <div className="flex justify-end gap-3">
                <button
                    className="px-4 py-2 text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200">Cancel
                </button>
                <button
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 shadow-sm transition-colors">Save
                    Changes
                </button>
            </div>
        </div>
    );
}