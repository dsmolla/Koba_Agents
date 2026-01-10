import {useState, useRef, useEffect} from 'react';
import {Send, Paperclip, Bot, User, FileText, Image, Film, Music, X} from 'lucide-react';
import Markdown from "react-markdown";
import {downloadFile} from "../../lib/fileService.js";

export default function ChatView({ messages, sendMessage, status, isConnected }) {
    const [inputText, setInputText] = useState("");
    const [stagedFiles, setStagedFiles] = useState([]);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({behavior: "instant"});
    }, [messages]);

    const handleSend = (e) => {
        e.preventDefault();
        if (!inputText.trim() && stagedFiles.length === 0) return;

        sendMessage(inputText, stagedFiles)

        setInputText("");
        setStagedFiles([]);
    };

    const handleFileClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e) => {
        const files = Array.from(e.target.files || []);
        console.error(files)
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
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div
                        key={ idx }
                        className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`flex items-start max-w-[80%] ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
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
                                {msg.content && <p className="text-sm whitespace-pre-wrap"><Markdown>{msg.content}</Markdown></p>}
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
                  className="p-4 bg-secondary-dark-bg border-t border-dark-border">
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
                    <input
                        type="text"
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        placeholder="Type your message..."
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