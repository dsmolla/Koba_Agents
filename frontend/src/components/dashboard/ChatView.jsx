import {useState, useRef, useEffect, memo} from 'react';
import {Send, Paperclip, Bot, User, FileText, Image, Film, Music, X, Trash2} from 'lucide-react';
import Markdown from "react-markdown";
import {downloadFile} from "../../lib/fileService.js";

// Memoized message bubble — only re-renders when its own message data changes,
// not when other messages in the list update (e.g., during streaming of the latest message).
const MessageBubble = memo(function MessageBubble({ msg, getFileIcon }) {
    return (
        <div className={`flex w-full mb-4 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex items-start ${msg.sender === 'user' ? 'max-w-[80%] flex-row-reverse' : 'max-w-full flex-row'} min-w-0`}>
                {msg.sender === 'user' && (
                    <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-blue-400 ml-2">
                        <User size={16} className="text-white"/>
                    </div>
                )}

                <div className={`p-3 rounded-xl overflow-hidden min-w-0 ${
                    msg.sender === 'user'
                        ? 'bg-blue-500 text-white rounded-tr-none'
                        : 'bg-gray-700 text-white rounded-tl-none'
                }`}>
                    {msg.content && (
                        <Markdown
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
                </div>
            </div>
        </div>
    );
});

const TypingIndicator = memo(function TypingIndicator() {
    return (
        <div className="flex w-full mb-4 justify-start">
            <div className="flex items-start flex-row max-w-full min-w-0">
                <div className="p-3 rounded-xl bg-gray-700 text-white rounded-tl-none">
                    <div className="flex gap-1 items-center h-5">
                        <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce"></span>
                    </div>
                </div>
            </div>
        </div>
    );
});

export default function ChatView({ messages, sendMessage, clearMessages, status, isConnected, isTyping = false, files = [] }) {
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
                // Only use API default if the user has no stored preference
                if (!localStorage.getItem('selectedModel')) {
                    setSelectedModel(data.default);
                }
            })
            .catch(err => console.error("Failed to fetch models:", err));
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({behavior: "instant"});
    }, [messages, isTyping]);

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
        const files = Array.from(e.target.files || []);
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
                <div className="relative border border-gray-600 rounded-md bg-gray-700/50 hover:bg-gray-700 transition-colors group">
                    <select
                        value={selectedModel}
                        onChange={(e) => {
                            setSelectedModel(e.target.value);
                            localStorage.setItem('selectedModel', e.target.value);
                        }}
                        className="text-xs font-medium bg-transparent text-zinc-200 border-none outline-none appearance-none cursor-pointer pl-3 pr-8 py-1.5 w-full block"
                        title="Select model"
                    >
                        {models.map(m => (
                            <option key={m.id} value={m.id} className="bg-gray-800 text-zinc-200 text-xs">
                                {m.name}
                            </option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-zinc-400 group-hover:text-zinc-200 transition-colors">
                        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                            <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                        </svg>
                    </div>
                </div>
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
                    <MessageBubble
                        key={idx}
                        msg={msg}
                        getFileIcon={getFileIcon}
                    />
                ))}
                {isTyping && <TypingIndicator />}
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
                  className="p-2 md:p-4 bg-secondary-dark-bg border-t border-dark-border relative flex flex-col gap-2">
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
                <div className="flex flex-wrap md:flex-nowrap items-center gap-2">
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
                            className="p-1.5 md:p-2 shrink-0 text-zinc-300 hover:text-zinc-100 transition-colors"
                            title="Attach file"
                        >
                            <Paperclip size={20}/>
                        </button>
                    </div>
                    <div className="flex items-center w-full md:w-auto flex-1 gap-2">
                        <input
                            type="text"
                            ref={inputRef}
                            value={inputText}
                            onChange={handleInputChange}
                            placeholder="Type your message... (@ to reference files)"
                            className="text-sm rounded-lg block w-full flex-1 p-2.5 bg-dark-input-bg border-gray-600 placeholder-dark-input-placeholder text-white outline-none min-w-0"
                        />
                        <button
                            type="submit"
                            disabled={!isConnected || (isConnected && !inputText.trim() && stagedFiles.length === 0)}
                            className="p-2 sm:px-3 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0 flex-none"
                        >
                            <Send size={20}/>
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
}