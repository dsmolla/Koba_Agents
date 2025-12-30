import {useState, useRef, useEffect} from 'react';
import {Send, Paperclip, Bot, User, FileText, Image, Film, Music, X} from 'lucide-react';

export default function ChatView() {
    const [messages, setMessages] = useState([
        {id: 1, text: "Hello! How can I help you today?", sender: 'bot', timestamp: new Date()}
    ]);
    const [inputText, setInputText] = useState("");
    const [stagedFiles, setStagedFiles] = useState([]);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({behavior: "smooth"});
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = (e) => {
        e.preventDefault();
        if (!inputText.trim() && stagedFiles.length === 0) return;

        const timestamp = new Date();
        const newMessages = [];

        // Add text message if it exists
        if (inputText.trim()) {
            newMessages.push({
                id: Date.now(),
                text: inputText,
                sender: 'user',
                timestamp: timestamp
            });
        }

        // Add staged files as messages
        stagedFiles.forEach((file, index) => {
            newMessages.push({
                id: Date.now() + index + 1,
                text: `Sent a file: ${file.name}`,
                sender: 'user',
                timestamp: timestamp,
                isFile: true,
                fileName: file.name,
                fileSize: (file.size / 1024 / 1024).toFixed(2) + ' MB',
                fileType: file.type.split('/')[0] || 'unknown'
            });
        });

        setMessages(prev => [...prev, ...newMessages]);
        
        // Clear inputs
        setInputText("");
        setStagedFiles([]);

        // Simulate bot response
        setTimeout(() => {
            let botText = "I received your message.";
            if (stagedFiles.length > 0) {
                botText += ` I've also received ${stagedFiles.length} file(s): ${stagedFiles.map(f => f.name).join(', ')}.`;
            }

            setMessages(prev => [...prev, {
                id: prev.length + 100,
                text: botText + " I am a stateless bot, so this conversation will disappear when you leave.",
                sender: 'bot',
                timestamp: new Date()
            }]);
        }, 1000);
    };

    const handleFileClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e) => {
        const files = Array.from(e.target.files || []);
        if (files.length === 0) return;

        setStagedFiles(prev => [...prev, ...files]);
        e.target.value = null; // Reset input so same file can be selected again if removed
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
                {messages.map((msg) => (
                    <div
                        key={msg.id}
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
                                {msg.isFile ? (
                                    <div className="flex items-center gap-3 min-w-50">
                                        <div className="p-2 bg-white/30 rounded-lg">
                                            {getFileIcon(msg.fileType, 24)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">{msg.fileName}</p>
                                            <p className="text-xs opacity-85">{msg.fileSize}</p>
                                        </div>
                                    </div>
                                ) : (
                                    <p className="text-sm">{msg.text}</p>
                                )}
                                <span className="text-xs opacity-85 mt-1 block">
                  {msg.timestamp.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
                </span>
                            </div>
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef}/>
            </div>

            {/* Staged Files Preview */}
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
                        disabled={!inputText.trim() && stagedFiles.length === 0}
                        className="p-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send size={20}/>
                    </button>
                </div>
            </form>
        </div>
    );
}