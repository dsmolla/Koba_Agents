import {useState, useRef, useEffect, memo} from 'react';
import {Send, Paperclip, Bot, User, FileText, Image, Film, Music, X, Trash2} from 'lucide-react';
import Markdown from "react-markdown";
import toast from "react-hot-toast";
import {downloadFile} from "../../lib/fileService.js";

const _ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'application/pdf', 'text/plain', 'text/csv']);
const _MAX_SIZE = 10 * 1024 * 1024; // 10 MB

// Memoized message bubble — only re-renders when its own message data changes,
// not when other messages in the list update (e.g., during streaming of the latest message).
const MessageBubble = memo(function MessageBubble({ msg, getFileIcon }) {
    return (
        <div className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex items-start max-w-[80%] ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                    msg.sender === 'user' ? 'bg-blue-400 ml-2' : 'bg-green-400 mr-2'
                }`}>
                    {msg.sender === 'user' ? <User size={16} className="text-white"/> :
                        <Bot size={16} className="text-white"/>}
                </div>

                <div className={`p-3 rounded-xl ${
                    msg.sender === 'user'
                        ? 'bg-blue-500 text-white rounded-tr-none'
                        : 'bg-gray-700 text-white rounded-tl-none'
                }`}>
                    {msg.content && (
                        <Markdown
                            skipHtml={true}
                            components={{
                                p: ({node, children, ...props}) => (
                                    <p className="text-sm whitespace-pre-wrap" {...props}>{children}</p>
                                )
                            }}
                        >
                            {msg.content}
                        </Markdown>
                    )}
                    {msg.files && msg.files.length > 0 && (
                        <div className={`flex flex-col gap-2 ${msg.content ? 'mt-2' : ''}`}>
                            {msg.files.map((file, idx) => (
                                <div key={file?.id || idx} className="flex items-center gap-3 bg-black/20 p-2 rounded-lg cursor-pointer hover:bg-black/50" onClick={() => downloadFile(file)}>
                                    <div className="p-2 bg-white/20 rounded-lg shrink-0">
                                        {getFileIcon(file.mime_type?.split('/')[0], 24)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">{file.filename}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                    <span className="text-xs opacity-75 mt-1 block text-right">
                        {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}) : ''}
                    </span>
                </div>
            </div>
        </div>
    );
});

export default function ChatView({ messages, sendMessage, clearMessages, status, isConnected, files = [] }) {
    const [inputText, setInputText] = useState("");
    const [stagedFiles, setStagedFiles] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [selectedModel, setSelectedModel] = useState(
        () => localStorage.getItem('selectedModel') || ''
    );
    const [models, setModels] = useState([]);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const inputRef = useRef(null);

    useEffect(() => {
        const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
        fetch(`${backendUrl}/models`)
            .then(res => res.json())
            .then(data => {
                setModels(data.models);
                // Use stored model only if it's in the valid list, otherwise fall back to API default
                const validIds = new Set(data.models.map(m => m.id));
                const stored = localStorage.getItem('selectedModel');
                setSelectedModel(validIds.has(stored) ? stored : data.default);
            })
            .catch(err => console.error("Failed to fetch models:", err));
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({behavior: "instant"});
    }, [messages]);

    const handleSend = (e) => {
        e.preventDefault();
        if (!inputText.trim() && stagedFiles.length === 0) return;

        const referencedFiles = files.filter(file =>
            inputText.includes(`@${file.filename}`)
        );

        sendMessage(inputText, stagedFiles, referencedFiles, selectedModel || null)

        setInputText("");
        setStagedFiles([]);
    };

    const handleInputChange = (e) => {
        const text = e.target.value;
        setInputText(text);

        const lastAt = text.lastIndexOf('@');
        if (lastAt !== -1) {
            const isStart = lastAt === 0;
            const isPrecededBySpace = !isStart && text[lastAt - 1] === ' ';

            if (isStart || isPrecededBySpace) {
                const query = text.slice(lastAt + 1);
                if (!query.includes(' ')) {
                    const matches = files.filter(f =>
                        f.filename.toLowerCase().startsWith(query.toLowerCase())
                    );
                    setSuggestions(matches);
                    setShowSuggestions(matches.length > 0);
                    return;
                }
            }
        }
        setShowSuggestions(false);
    };

    const insertSuggestion = (filename) => {
        const lastAt = inputText.lastIndexOf('@');
        if (lastAt !== -1) {
            const prefix = inputText.slice(0, lastAt);
            setInputText(`${prefix}@${filename} `);
            setShowSuggestions(false);
            inputRef.current?.focus();
        }
    };

    const handleFileClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e) => {
        const files = Array.from(e.target.files || []).filter(file => {
            if (!_ALLOWED_TYPES.has(file.type)) {
                toast.error(`${file.name}: file type not allowed`);
                return false;
            }
            if (file.size > _MAX_SIZE) {
                toast.error(`${file.name}: exceeds 10MB limit`);
                return false;
            }
            return true;
        });
        if (files.length === 0) return;

        setStagedFiles(prev => [...prev, ...files]);
        e.target.value = null;
    };

    const removeFile = (indexToRemove) => {
        setStagedFiles(prev => prev.filter((_, index) => index !== indexToRemove));
    };

    const getFileIcon = (type, size = 24) => {
        if (type === 'image') return <Image size={size} className="text-purple-500"/>;
        if (type === 'video') return <Film size={size} className="text-red-500"/>;
        if (type === 'audio') return <Music size={size} className="text-yellow-500"/>;
        return <FileText size={size} className="text-blue-500"/>;
    };

    return (
        <div
            className="flex flex-col h-full bg-secondary-dark-bg rounded-lg shadow-sm border border-dark-border overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 border-b border-dark-border bg-gray-800/50">
                <span className="text-sm font-medium text-zinc-300">Chat</span>
                <button
                    onClick={clearMessages}
                    className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-zinc-400 hover:text-red-400 hover:cursor-pointer hover:bg-red-400/10 rounded transition-colors"
                    title="Clear chat"
                >
                    <Trash2 size={14} />
                    Clear Chat
                </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    // Use timestamp+sender as key — stable identity prevents full-list reconciliation
                    // when new messages arrive. Falls back to index only if timestamps are missing.
                    <MessageBubble
                        key={msg.timestamp ? `${msg.timestamp}-${msg.sender}` : idx}
                        msg={msg}
                        getFileIcon={getFileIcon}
                    />
                ))}
                <div ref={messagesEndRef}/>
            </div>

            {status && (
                <div className="px-4 py-2 bg-secondary-dark-bg text-xs text-zinc-400 flex items-center gap-2 border-t border-dark-border">
                    {status.icon && <span className="text-base">{status.icon}</span>}
                    <span>{status.content}</span>
                </div>
            )}

            {stagedFiles.length > 0 && (
                <div className="px-4 py-2 flex flex-wrap gap-2 border-t border-dark-border bg-secondary-dark-bg">
                    {stagedFiles.map((file, index) => (
                        <div key={index} className="flex items-center gap-2 bg-gray-700 px-3 py-1 rounded-full text-white text-xs border border-gray-600">
                            <span className="truncate max-w-37.5">{file.name}</span>
                            <button onClick={() => removeFile(index)} className="hover:text-red-400">
                                <X size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <form onSubmit={handleSend}
                  className="p-4 bg-secondary-dark-bg border-t border-dark-border relative">
                {showSuggestions && (
                    <div className="absolute bottom-full left-0 w-full mb-2 bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-48 overflow-y-auto z-10 mx-4">
                        {suggestions.map((file) => (
                            <div
                                key={file.id}
                                className="flex items-center gap-2 p-2 hover:bg-gray-700 cursor-pointer text-gray-200"
                                onClick={() => insertSuggestion(file.filename)}
                            >
                                {getFileIcon(file.mime_type?.split('/')[0], 16)}
                                <span className="text-sm truncate">{file.filename}</span>
                            </div>
                        ))}
                    </div>
                )}
                <div className="flex items-center gap-2">
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        multiple
                        onChange={handleFileChange}
                    />
                    <button
                        type="button"
                        onClick={handleFileClick}
                        className="p-2 text-zinc-300 hover:text-zinc-100 transition-colors"
                        title="Attach file"
                    >
                        <Paperclip size={20}/>
                    </button>
                    <select
                        value={selectedModel}
                        onChange={(e) => {
                            setSelectedModel(e.target.value);
                            localStorage.setItem('selectedModel', e.target.value);
                        }}
                        className="text-xs bg-dark-input-bg text-zinc-300 border border-gray-600 rounded-md px-2 py-2 outline-none appearance-none cursor-pointer hover:border-gray-500 transition-colors"
                        title="Select model"
                    >
                        {models.map(m => (
                            <option key={m.id} value={m.id}>
                                {m.name}
                            </option>
                        ))}
                    </select>
                    <input
                        type="text"
                        ref={inputRef}
                        value={inputText}
                        onChange={handleInputChange}
                        placeholder="Type your message... (@ to reference files)"
                        className="text-sm rounded-lg block w-full p-2.5 bg-dark-input-bg border-gray-600 placeholder-dark-input-placeholder text-white outline-none"
                    />
                    <button
                        type="submit"
                        disabled={!isConnected || (isConnected && !inputText.trim() && stagedFiles.length === 0)}
                        className="p-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send size={20}/>
                    </button>
                </div>
            </form>
        </div>
    );
}