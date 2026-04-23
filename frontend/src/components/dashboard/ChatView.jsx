import { useState, useRef, useEffect, memo } from 'react';
import { Send, Paperclip, Bot, User, FileText, Image, Film, Music, X, Trash2 } from 'lucide-react';
import Markdown from "react-markdown";
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { downloadFile } from "../../lib/fileService.js";

// Memoized message bubble — only re-renders when its own message data changes,
// not when other messages in the list update (e.g., during streaming of the latest message).
const MessageBubble = memo(function MessageBubble({ msg, getFileIcon, sendApproval }) {
    if (msg.type === 'approval_required') {
        return (
            <div className="flex w-full mb-4 justify-start">
                <div className="flex items-start flex-row max-w-full min-w-0">
                    <div className="p-4 rounded-xl bg-secondary-dark-bg border border-yellow-600/50 shadow-lg min-w-[300px] max-w-full">
                        <div className="flex items-center gap-2 mb-3">
                            <div className="w-8 h-8 rounded-full bg-yellow-500/20 flex items-center justify-center shrink-0">
                                <span className="text-yellow-500 text-lg">⚠️</span>
                            </div>
                            <h3 className="text-white font-medium">Action Approval Required</h3>
                        </div>
                        <div className="bg-primary-dark-bg/50 rounded p-3 mb-4 text-sm text-gray-300">
                            <p className="font-semibold mb-1 capitalize text-gray-100">{msg.confirmation}</p>
                            <pre className="whitespace-pre-wrap font-mono text-xs overflow-x-auto text-primary-300">
                                {msg.data}
                            </pre>
                        </div>
                        <div className="flex gap-3 mt-4">
                            <button
                                onClick={() => sendApproval(true, msg.id)}
                                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer"
                            >
                                Approve
                            </button>
                            <button
                                onClick={() => sendApproval(false, msg.id)}
                                className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer"
                            >
                                Reject
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className={`flex w-full mb-4 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex items-start ${msg.sender === 'user' ? 'max-w-[80%] flex-row-reverse' : 'max-w-full flex-row'} min-w-0`}>
                {msg.sender === 'user' && (
                    <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-primary-400 ml-2">
                        <User size={16} className="text-white" />
                    </div>
                )}

                <div className={`p-4 rounded-xl overflow-hidden min-w-0 ${msg.sender === 'user'
                        ? 'bg-primary-600 text-white rounded-tr-none shadow-md shadow-primary-500/20'
                        : 'bg-primary-900/60 border border-primary-800/40 text-primary-50 rounded-tl-none backdrop-blur-sm'
                    }`}>
                    {msg.content && (
                        <Markdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                p: ({ node, ...props }) => (
                                    <p className="text-sm my-2 whitespace-pre-wrap leading-relaxed" {...props} />
                                ),
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
                                            <div className="bg-secondary-dark-bg/90 px-4 py-2 text-xs text-dark-input-placeholder font-mono uppercase border-b border-white/10 flex justify-between items-center">
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
                <div className="p-4 rounded-xl bg-primary-900/60 border border-primary-800/40 text-primary-50 rounded-tl-none backdrop-blur-sm">
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

export default function ChatView({ messages, sendMessage, sendApproval, clearMessages, status, isConnected, isTyping = false, files = [] }) {
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
        messagesEndRef.current?.scrollIntoView({ behavior: "instant" });
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
        if (type === 'image') return <Image size={size} className="text-purple-500" />;
        if (type === 'video') return <Film size={size} className="text-red-500" />;
        if (type === 'audio') return <Music size={size} className="text-yellow-500" />;
        return <FileText size={size} className="text-blue-500" />;
    };

    return (
        <div
            className="flex flex-col h-full bg-secondary-dark-bg backdrop-blur-md rounded-2xl shadow-xl border border-dark-border overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-dark-border bg-primary-950/60">
                <div className="relative border border-primary-800/50 rounded-xl bg-primary-900/40 hover:bg-primary-800/40 transition-colors group">
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
                            <option key={m.id} value={m.id} className="bg-dark-input-bg text-zinc-200 text-xs">
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
                        sendApproval={sendApproval}
                    />
                ))}
                {isTyping && <TypingIndicator />}
                <div ref={messagesEndRef} />
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
                        <div key={index} className="flex items-center gap-2 bg-dark-input-bg px-3 py-1 rounded-full text-white text-xs border border-dark-input-border">
                            <span className="truncate max-w-37.5">{file.name}</span>
                            <button onClick={() => removeFile(index)} className="hover:text-red-400">
                                <X size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            <form onSubmit={handleSend}
                className="p-3 md:p-5 bg-primary-dark-bg/60 backdrop-blur-md border-t border-dark-border relative flex flex-col gap-2">
                {showSuggestions && (
                    <div className="absolute bottom-full left-0 w-full mb-2 bg-primary-950/90 backdrop-blur-lg border border-primary-800/50 rounded-xl shadow-2xl shadow-primary-900/20 max-h-48 overflow-y-auto z-10 mx-4">
                        {suggestions.map((file) => (
                            <div
                                key={file.id}
                                className="flex items-center gap-2 p-2 hover:bg-dark-input-bg cursor-pointer text-gray-200"
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
                            <Paperclip size={20} />
                        </button>
                    </div>
                    <div className="flex items-center w-full md:w-auto flex-1 gap-2">
                        <input
                            type="text"
                            ref={inputRef}
                            value={inputText}
                            onChange={handleInputChange}
                            placeholder="Type your message... (@ to reference files)"
                            className="text-sm rounded-lg block w-full flex-1 p-2.5 bg-dark-input-bg border-dark-input-border placeholder-dark-input-placeholder text-white outline-none min-w-0"
                        />
                        <button
                            type="submit"
                            disabled={!isConnected || (isConnected && !inputText.trim() && stagedFiles.length === 0)}
                            className="p-2 sm:px-3 bg-primary-500 text-white rounded-md hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0 flex-none"
                        >
                            <Send size={20} />
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
}