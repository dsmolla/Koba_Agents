import React from 'react';
import { Link } from 'react-router-dom';

function PrivacyPolicy() {
    return (
        <div className="min-h-screen bg-primary-dark-bg text-gray-300 py-12 px-4 sm:px-6 lg:px-8 font-sans leading-relaxed">
            <div className="max-w-3xl mx-auto bg-secondary-dark-bg shadow-2xl rounded-2xl p-8 border border-dark-border">

                <div className="mb-8 border-b border-dark-border pb-4 flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-white tracking-tight">Privacy Policy</h1>
                        <p className="mt-1 text-sm text-gray-400">For Koba Agents</p>
                    </div>
                    <Link to="/login" className="text-sm font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
                        ← Back to Login
                    </Link>
                </div>

                <div className="space-y-6 text-sm text-gray-400">
                    <p>
                        <strong className="text-gray-300">Effective Date:</strong> April 23, 2026<br />
                    </p>

                    <p>
                        Welcome to <strong className="text-gray-300">Koba Agents</strong>. We are committed to protecting your personal information and your right to privacy. This Privacy Policy explains how we collect, use, and safeguard your information—particularly your sensitive Google Workspace data—when you use our website, application, and services (collectively, the "Services").
                    </p>
                    <p>
                        Koba Agents is an AI-powered assistant designed to integrate with your Google Workspace. Because of the powerful nature of these integrations, <strong className="text-gray-300">data privacy and transparency are our highest priorities.</strong>
                    </p>

                    <hr className="border-dark-border my-8" />

                    <h2 className="text-xl font-semibold text-white mt-8 mb-4 tracking-tight">1. Information We Collect</h2>
                    <p>We collect information directly from you when you register, as well as data gathered dynamically when you use our core services.</p>

                    <h3 className="text-lg font-medium text-white mt-6">A. Account Information</h3>
                    <p>When you request an invitation and register an account, we collect:</p>
                    <ul className="list-disc pl-5 space-y-1">
                        <li><strong className="text-gray-300">Personal details</strong>: Your full name and email address.</li>
                        <li><strong className="text-gray-300">Authentication data</strong>: Encrypted passwords (if you do not use Google Single Sign-On).</li>
                    </ul>

                    <h3 className="text-lg font-medium text-white mt-6">B. Google Workspace Data</h3>
                    <p>To provide our core AI-agent capabilities, Koba Agents requires <strong className="text-gray-300">OAuth2 authorization</strong> to access specific Google APIs on your behalf. Depending on the permissions you grant, we temporarily process:</p>
                    <ul className="list-disc pl-5 space-y-1">
                        <li><strong className="text-gray-300">Gmail</strong>: Email contents, metadata, and draft information.</li>
                        <li><strong className="text-gray-300">Google Calendar</strong>: Event details, schedules, and availability.</li>
                        <li><strong className="text-gray-300">Google Drive, Docs & Sheets</strong>: File contents, metadata, and spreadsheet data.</li>
                        <li><strong className="text-gray-300">Google Tasks</strong>: Task lists and statuses.</li>
                    </ul>

                    <div className="bg-primary-900 border border-primary-700/50 rounded-lg p-4 mt-4">
                        <p className="text-primary-100 m-0"><strong>Important Note:</strong> Koba Agents processes this workspace data <em>strictly</em> to fulfill your direct commands and automated workflows.</p>
                    </div>

                    <h3 className="text-lg font-medium text-white mt-6">C. Usage and Chat Data</h3>
                    <ul className="list-disc pl-5 space-y-1">
                        <li><strong className="text-gray-300">Conversational History:</strong> Prompts, commands, and chat interactions you have with the AI assistant.</li>
                        <li><strong className="text-gray-300">Memories:</strong> User preferences and specific facts you instruct the AI to remember to improve future interactions.</li>
                    </ul>

                    <h3 className="text-lg font-medium text-white mt-6">D. User-Uploaded Files</h3>
                    <p>When you use the File Manager, you may manually upload files (such as images, videos, or documents) directly to our platform to be managed or interacted with by your AI agents.</p>

                    <hr className="border-dark-border my-8" />

                    <h2 className="text-xl font-semibold text-white mt-8 mb-4 tracking-tight">2. How We Use Your Information</h2>
                    <ul className="list-disc pl-5 space-y-2">
                        <li><strong className="text-gray-300">Providing the Service:</strong> To orchestrate sub-agents that intelligently execute your commands (e.g., drafting emails, analyzing spreadsheets).</li>
                        <li><strong className="text-gray-300">AI Processing:</strong> To formulate prompts. Your queries and relevant context from your Workspace are sent securely to our designated Large Language Model (LLM) providers (e.g., Google Generative AI) for processing.</li>
                        <li><strong className="text-gray-300">Automated Workflows:</strong> To run persistent background tasks, such as our Gmail Auto-Reply webhook system, strictly based on the rules you define.</li>
                        <li><strong className="text-gray-300">Account Management:</strong> To verify your identity, send transactional emails (like invitation codes or password resets), and enforce security protocols.</li>
                    </ul>

                    <hr className="border-dark-border my-8" />

                    <h2 className="text-xl font-semibold text-white mt-8 mb-4 tracking-tight">3. How Your Data is Shared and Processed</h2>
                    <p>We do <strong className="text-gray-300">not</strong> sell your personal data. We only share information with critical infrastructure partners necessary to operate the application.</p>
                    <ul className="list-disc pl-5 space-y-2">
                        <li><strong className="text-gray-300">Large Language Models (LLMs):</strong> Temporary workspace context is transmitted to our LLM providers to generate responses. We ensure our API agreements prohibit LLM providers from using your workspace data to train their fundamental public models.</li>
                        <li><strong className="text-gray-300">Supabase (Database Engine & Storage):</strong> Your account data, encrypted OAuth tokens, agent chat histories, and any manually uploaded files are securely stored and encrypted at rest using Supabase infrastructure.</li>
                        <li><strong className="text-gray-300">Google Cloud Platform (GCP):</strong> We utilize highly secure, enterprise-grade Google Cloud infrastructure to operate our backend operations, route notifications securely, and manage server traffic.</li>
                    </ul>

                    <hr className="border-dark-border my-8" />

                    <h2 className="text-xl font-semibold text-white mt-8 mb-4 tracking-tight">4. How We Secure Your Data</h2>
                    <ul className="list-disc pl-5 space-y-2">
                        <li><strong className="text-gray-300">Encrypted Tokens:</strong> Your Google OAuth access and refresh tokens are highly encrypted <em className="text-gray-300">at rest</em> within our database.</li>
                        <li><strong className="text-gray-300">Row Level Security (RLS):</strong> Our database employs strict Row Level Security, ensuring that you (and the agents acting on your behalf) can only query and access your specific data.</li>
                        <li><strong className="text-gray-300">Invitation-Only Access:</strong> Access to the platform is heavily restricted via database-level triggers. No unauthorized party can create an account without a valid verification code explicitly generated by Koba Agents administrators.</li>
                        <li><strong className="text-gray-300">No Extraneous Storage:</strong> We do not permanently copy or store the contents of your Google Drive, Docs, or Gmail inbox on our servers. Workspace data is fetched dynamically into system memory solely for the brief duration required to complete your AI request.</li>
                    </ul>

                    <hr className="border-dark-border my-8" />

                    <h2 className="text-xl font-semibold text-white mt-8 mb-4 tracking-tight">5. Google API Services User Data Policy Compliance</h2>
                    <p>Koba Agents' use and transfer of information received from Google APIs to any other app will adhere to the <a href="https://developers.google.com/terms/api-services-user-data-policy" className="text-primary-400 hover:text-primary-300 transition-colors font-medium underline underline-offset-2" target="_blank" rel="noopener noreferrer">Google API Services User Data Policy</a>, including the Limited Use requirements.</p>
                    <ul className="list-disc pl-5 space-y-2 mt-4">
                        <li>Workspace data fetched via Google APIs is used <em className="text-gray-300">only</em> to provide or improve user-facing features.</li>
                        <li>We do not use or transfer your workspace data for serving ads.</li>
                        <li>Access to your Workspace data by human administrators is strictly prohibited unless explicitly authorized by you for troubleshooting purposes.</li>
                    </ul>

                    <hr className="border-dark-border my-8" />

                    <h2 className="text-xl font-semibold text-white mt-8 mb-4 tracking-tight">6. Your Rights and Choices</h2>
                    <p>You have full control over your data:</p>
                    <ul className="list-disc pl-5 space-y-2">
                        <li><strong className="text-gray-300">Clear Chat History:</strong> You can instantly and permanently delete your entire conversation history at any time using the "Clear Chat" feature built directly into the user interface.</li>
                        <li><strong className="text-gray-300">Revoke Access:</strong> You may revoke Koba Agents' access to your Google account at any time via your Google Account Security Dashboard. Doing so will immediately disable the AI's ability to interface with your Workspace.</li>
                        <li><strong className="text-gray-300">File Management:</strong> You maintain full ownership of all manually uploaded files. You can view, download, or permanently delete them at any time via the File Manager dashboard.</li>
                        <li><strong className="text-gray-300">Delete Memories:</strong> You can instruct the agent to forget specific preferences via the chat interface, which permanently deletes them from our Redis/Supabase storage.</li>
                        <li><strong className="text-gray-300">Account Deletion:</strong> You may contact us at any time to request the complete deletion of your account and all associated encrypted tokens.</li>
                    </ul>

                    <hr className="border-dark-border my-8" />

                    <h2 className="text-xl font-semibold text-white mt-8 mb-4 tracking-tight">7. Contact Us</h2>
                    <p>If you have any questions or concerns about this Privacy Policy, please contact us at:</p>
                    <p className="bg-primary-dark-bg inline-block px-4 py-2 rounded-md border border-dark-border">
                        <strong className="text-gray-300">Koba Agents Support</strong><br />
                        Email: <a href="mailto:support@koba-agents.com" className="text-primary-400 hover:text-primary-300 transition-colors font-medium">support@koba-agents.com</a>
                    </p>
                </div>

            </div>
        </div>
    );
}

export default PrivacyPolicy;
