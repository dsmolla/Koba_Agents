import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Bot, User, FileText, Image, Film, Music } from 'lucide-react';

export default function ChatView() {
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! How can I help you today?", sender: 'bot', timestamp: new Date() }
  ]);
  const [inputText, setInputText] = useState("");
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const newUserMsg = {
      id: messages.length + 1,
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMsg]);
    setInputText("");

    // Simulate bot response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: prev.length + 1,
        text: "I received your message. I am a stateless bot, so this conversation will disappear when you leave.",
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

    const newMessages = files.map((file, index) => ({
      id: messages.length + 1 + index,
      text: `Sent a file: ${file.name}`,
      sender: 'user',
      timestamp: new Date(),
      isFile: true,
      fileName: file.name,
      fileSize: (file.size / 1024 / 1024).toFixed(2) + ' MB',
      fileType: file.type.split('/')[0] || 'unknown'
    }));

    setMessages(prev => [...prev, ...newMessages]);
    e.target.value = null;

    // Simulate bot response
    setTimeout(() => {
        const fileNames = files.map(f => f.name).join(', ');
        setMessages(prev => [...prev, {
          id: prev.length + 1,
          text: `I received your files: ${fileNames}.`,
          sender: 'bot',
          timestamp: new Date()
        }]);
      }, 1000);
  };

  const getFileIcon = (type, size = 24) => {
    if (type === 'image') return <Image size={size} className="text-purple-500" />;
    if (type === 'video') return <Film size={size} className="text-red-500" />;
    if (type === 'audio') return <Music size={size} className="text-yellow-500" />;
    return <FileText size={size} className="text-blue-500" />;
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-zinc-900 rounded-lg shadow-sm border border-zinc-200 dark:border-zinc-800 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex items-start max-w-[80%] ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                msg.sender === 'user' ? 'bg-blue-500 ml-2' : 'bg-green-500 mr-2'
              }`}>
                {msg.sender === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
              </div>

              <div className={`p-3 rounded-lg ${
                msg.sender === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-none' 
                  : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-tl-none'
              }`}>
                {msg.isFile ? (
                  <div className="flex items-center gap-3 min-w-[200px]">
                    <div className="p-2 bg-white/20 rounded-lg">
                      {getFileIcon(msg.fileType, 24)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{msg.fileName}</p>
                      <p className="text-xs opacity-70">{msg.fileSize}</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm">{msg.text}</p>
                )}
                <span className="text-xs opacity-70 mt-1 block">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="p-4 bg-white dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-800">
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
            className="p-2 text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200 transition-colors"
            title="Attach file"
          >
            <Paperclip size={20} />
          </button>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 p-2 bg-zinc-50 dark:bg-zinc-800 border-none rounded-md focus:ring-2 focus:ring-blue-500 outline-none text-zinc-900 dark:text-zinc-100"
          />
          <button
            type="submit"
            disabled={!inputText.trim()}
            className="p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  );
}
