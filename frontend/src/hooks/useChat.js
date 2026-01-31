import {useState, useEffect, useRef, useCallback} from 'react';
import {useAuth} from "./useAuth.js";
import {uploadFiles} from "../lib/fileService.js";

export const useChat = () => {
    const [messages, setMessages] = useState([]);
    const [status, setStatus] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef(null);
    const { session } = useAuth();

    const handleServerMessage = (data) => {
        switch (data.type) {
            case 'history':
                setMessages(data.messages);
                setStatus(null);
                break;

            case 'message':
                setMessages(messages => [...messages, {
                    sender: data.sender,
                    content: data.content,
                    files: data.files,
                    timestamp: data.timestamp
                }]);
                setStatus(null);
                break;

            case 'status':
                setStatus({content: data.content, icon: data.icon});
                break;

            case 'error':
                if (data.code === 'AUTH_REQUIRED') {
                    console.error("Auth required:", data.content);
                    alert(`Authentication Session Expired: ${data.content}`);
                    setStatus(null);
                } else {
                    alert(`Error: ${data.content}`);
                    setStatus(null);
                }
                break;

            default:
                console.warn("Unknown message type:", data.type);
        }
    };

    useEffect(() => {
        if (!session?.access_token) return;

        let socket = null;
        let reconnectTimeout = null;

        const connectWebSocket = async () => {
            try {
                const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
                
                // 1. Get a one-time ticket
                const ticketResponse = await fetch(`${backendUrl}/auth/ticket`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${session.access_token}`
                    }
                });

                if (!ticketResponse.ok) {
                    console.error("Failed to get WebSocket ticket. Status:", ticketResponse.status);
                    // If 401, the token might be expired. 
                    // Since 'session' comes from context, relying on AuthContext to update it on refresh.
                    // We'll retry in 5s hoping for a fresh token.
                    reconnectTimeout = setTimeout(connectWebSocket, 5000); 
                    return;
                }

                const { ticket } = await ticketResponse.json();

                const apiUrl = import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8000';
                const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
                const wsUrl = `${apiUrl}/ws/chat?ticket=${ticket}&timezone=${timezone}`;

                socket = new WebSocket(wsUrl);
                ws.current = socket;

                socket.onopen = () => {
                    setIsConnected(true);
                };

                socket.onclose = () => {
                    setIsConnected(false);
                    reconnectTimeout = setTimeout(connectWebSocket, 3000);
                };

                socket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    handleServerMessage(data);
                };
            } catch (error) {
                console.error("WebSocket connection error:", error);
                reconnectTimeout = setTimeout(connectWebSocket, 5000);
            }
        };

        connectWebSocket();

        return () => {
            if (socket) {
                socket.close();
            }
            if (reconnectTimeout) {
                clearTimeout(reconnectTimeout);
            }
        };
    }, [session?.access_token]); // Depend on access_token specifically to trigger reconnect on refresh

    const sendMessage = useCallback(async (text, stagedFiles = [], referencedFiles = []) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            const timestamp = Date.now();

            let uploadedFiles = [];
            if (stagedFiles.length > 0) {
                try {
                    setStatus({content: "Uploading files...", icon: "📤"});
                    uploadedFiles = await uploadFiles(session.user.id, stagedFiles)
                } catch {
                    alert("Failed to upload files. Please try again.");
                    setStatus(null);
                    return;
                }
            }

            const allFiles = [...uploadedFiles, ...referencedFiles];

            setMessages(prev => [...prev, {
                type: 'message',
                sender: 'user',
                content: text,
                files: allFiles,
                timestamp: timestamp
            }]);

            ws.current.send(JSON.stringify({
                type: 'message',
                sender: 'user',
                content: text,
                files: allFiles,
                timestamp: timestamp
            }));

            setStatus(null);
        } else {
            alert("Connection lost. Please wait...");
        }
    }, [session]);

    const clearMessages = useCallback(async () => {
        if (!session?.access_token) return;

        try {
            const apiUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/chat/clear`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${session.access_token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to clear chat history');
            }

            setMessages([]);
        } catch (error) {
            console.error('Error clearing chat:', error);
            alert('Failed to clear chat history');
        }
    }, [session]);

    return {messages, sendMessage, clearMessages, status, isConnected};
};