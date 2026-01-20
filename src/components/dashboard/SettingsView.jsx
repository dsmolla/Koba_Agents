import {useState} from 'react';
import {User, Mail, Shield, Bell, LogOut, Edit2, Check, X, Share2} from 'lucide-react';
import {signOutUser, updateUserData, signInWithGoogleProvider} from '../../lib/supabase';
import {useNavigate} from 'react-router-dom';
import toast, {Toaster} from "react-hot-toast";
import {GoogleDriveIcon, GmailIcon, GoogleCalendarIcon, GoogleTasksIcon} from "../../assets/icons.jsx";

export default function SettingsView({user}) {
    const navigate = useNavigate();
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({
        email: user?.email || '',
        fullName: user?.user_metadata?.full_name || ''
    });

    const handleConnectService = async (service, scope) => {
        try {
            await signInWithGoogleProvider(scope);
        } catch (error) {
            console.error(`Error connecting ${service}:`, error);
            toast.error(`Failed to connect ${service}`);
        }
    };

    const handleSignOut = async () => {
        try {
            await signOutUser();
            navigate('/login');
        } catch (error) {
            console.error("Error signing out:", error);
        }
    };

    const handleInputChange = (e) => {
        const {name, value} = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSaveProfile = async () => {
        try {
            await updateUserData({
                email: formData.email,
                fullName: formData.fullName,
            })

            setIsEditing(false);
            toast.success('Profile saved successfully.', {position: 'top-right'})

        } catch (error) {
            console.error("Error updating profile:", error);
            alert("Failed to update profile: " + error.message);
        }
    };

    const handleCancelEdit = () => {
        setIsEditing(false);
        // Reset form data
        if (user) {
            setFormData({
                email: user.email || '',
                fullName: user.user_metadata?.full_name || ''
            });
        }
    };

    if (!user) return <div className="text-white">Loading settings...</div>;

    return (
        <div className="max-w-2xl space-y-8">
            <Toaster/>
            <div>
                <h2 className="text-2xl font-bold text-white mb-6">Account Settings</h2>
                <div
                    className="bg-secondary-dark-bg rounded-lg shadow-sm border border-dark-border divide-y dark:divide-dark-border">
                    <div className="p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-medium text-white flex items-center gap-2">
                                <User size={20}/> Profile Information
                            </h3>
                            {!isEditing ? (
                                <button
                                    onClick={() => setIsEditing(true)}
                                    className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                                >
                                    <Edit2 size={16}/> Edit
                                </button>
                            ) : (
                                <div className="flex gap-2">
                                    <button
                                        onClick={handleSaveProfile}
                                        className="p-1 text-green-400 hover:bg-green-400/10 rounded transition-colors"
                                        title="Save"
                                    >
                                        <Check size={18}/>
                                    </button>
                                    <button
                                        onClick={handleCancelEdit}
                                        className="p-1 text-red-400 hover:bg-red-400/10 rounded transition-colors"
                                        title="Cancel"
                                    >
                                        <X size={18}/>
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-gray-200 mb-1">Email</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                                    <input
                                        type="email"
                                        name="email"
                                        value={formData.email}
                                        onChange={handleInputChange}
                                        disabled={!isEditing}
                                        className={`w-full pl-9 border ${isEditing ? 'border-blue-500/50 bg-dark-input-bg' : 'border-transparent bg-transparent'} text-white rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none transition-all`}
                                    />
                                </div>
                            </div>
                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-gray-200 mb-1">Full Name</label>
                                <input
                                    type="text"
                                    name="fullName"
                                    value={formData.fullName}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className={`w-full border ${isEditing ? 'border-blue-500/50 bg-dark-input-bg' : 'border-dark-input-border bg-dark-input-bg/50 text-gray-300'} text-white rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none transition-all`}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="p-6">
                        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                            <Share2 size={20}/> Integrations
                        </h3>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg mb-4">
                                <div>
                                    <p className="text-blue-100 font-medium">Connect All Services</p>
                                    <p className="text-sm text-blue-300">Grant access to all Google services at once</p>
                                </div>
                                <button
                                    onClick={() => handleConnectService('All Services', 'https://mail.google.com/ https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/tasks')}
                                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 hover:cursor-pointer text-sm font-medium transition-colors shadow-lg shadow-blue-900/20"
                                >
                                    Connect All
                                </button>
                            </div>

                            <div className="flex items-center justify-between p-3 bg-dark-input-bg/30 rounded-lg">
                                <div className='flex items-center'>
                                    <GmailIcon size={40} className='mr-2'/>
                                    <div>
                                        <p className="text-gray-200 font-medium">Gmail</p>
                                        <p className="text-sm text-gray-400">Connect to access your emails</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleConnectService('Gmail', 'https://mail.google.com/')}
                                    className="flex items-center gap-2 px-4 py-1.5 bg-google-dark text-white rounded hover:bg-google-hover hover:cursor-pointer text-sm font-medium transition-colors"
                                >
                                    Connect
                                </button>
                            </div>

                            <div className="flex items-center justify-between p-3 bg-dark-input-bg/30 rounded-lg">
                                <div className='flex items-center'>
                                    <GoogleCalendarIcon size={40} className="mr-2"/>
                                    <div>
                                        <p className="text-gray-200 font-medium">Google Calendar</p>
                                        <p className="text-sm text-gray-400">Connect to manage events</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleConnectService('Calendar', 'https://www.googleapis.com/auth/calendar')}
                                    className="flex items-center gap-2 px-4 py-1.5 bg-google-dark text-white rounded hover:bg-google-hover hover:cursor-pointer text-sm font-medium transition-colors"
                                >
                                    Connect
                                </button>
                            </div>

                            <div className="flex items-center justify-between p-3 bg-dark-input-bg/30 rounded-lg">
                                <div className='flex items-center'>
                                    <GoogleDriveIcon size={40} className="mr-2"/>
                                    <div>
                                        <p className="text-gray-200 font-medium">Google Drive</p>
                                        <p className="text-sm text-gray-400">Connect to access files</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleConnectService('Drive', 'https://www.googleapis.com/auth/drive')}
                                    className="flex items-center gap-2 px-4 py-1.5 bg-google-dark text-white rounded hover:bg-google-hover hover:cursor-pointer text-sm font-medium transition-colors"
                                >
                                    Connect
                                </button>
                            </div>

                            <div className="flex items-center justify-between p-3 bg-dark-input-bg/30 rounded-lg">
                                <div className='flex items-center'>
                                    <GoogleTasksIcon size={40} className="mr-2"/>
                                    <div>
                                        <p className="text-gray-200 font-medium">Google Tasks</p>
                                        <p className="text-sm text-gray-400">Connect to manage tasks</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleConnectService('Tasks', 'https://www.googleapis.com/auth/tasks')}
                                    className="flex items-center gap-2 px-4 py-1.5 bg-google-dark text-white rounded hover:bg-google-hover hover:cursor-pointer text-sm font-medium transition-colors"
                                >
                                    Connect
                                </button>
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
                            <LogOut size={20} className="text-red-500"/> Danger Zone
                        </h3>
                        <button
                            onClick={handleSignOut}
                            className="px-4 py-2 border border-red-500 text-red-500 rounded-md hover:bg-red-500/20 transition-colors text-sm font-medium"
                        >
                            Sign Out
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}