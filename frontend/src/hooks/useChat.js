import {useState, useEffect, useRef, useCallback} from 'react';
import {useAuth} from "./useAuth.js";
import {uploadFiles} from "../lib/fileService.js";

const MAX_MESSAGES = 100; // Cap in-memory message count; older messages remain in LangGraph

export const useChat = () => {
    const [messages, setMessages] = useState([]);
    const [status, setStatus] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const ws = useRef(null);
    const { session } = useAuth();

    // Keep a ref to the latest access token so reconnect logic can always use the current value
    // without making the WebSocket effect depend on token changes (which would disconnect on every refresh)
    const accessTokenRef = useRef(session?.access_token);
    useEffect(() => {
        accessTokenRef.current = session?.access_token;
    }, [session?.access_token]);

    const handleServerMessage = (data) => {
        switch (data.type) {
            case 'history':
                setMessages(data.messages);
                setStatus(null);
                break;

            case 'message':
                setIsTyping(false);
                setMessages(prev => {
                    const updated = [...prev, {
                        sender: data.sender,
                        content: data.content,
                        files: data.files,
                        timestamp: data.timestamp
                    }];
                    // Cap to MAX_MESSAGES to prevent unbounded memory growth
                    return updated.length > MAX_MESSAGES ? updated.slice(-MAX_MESSAGES) : updated;
                });
                setStatus(null);
                break;

            case 'status':
                setStatus({content: data.content, icon: data.icon});
                break;

            case 'error':
                setIsTyping(false);
                if (data.code === 'AUTH_REQUIRED') {
                    console.error("Auth required:", data.content);
                    alert(`Authentication Session Expired: ${data.content}`);
                    setStatus(null);
                } else {
                    alert(`Error: ${data.content}`);
                    setStatus(null);
                }
                break;

            case 'approval_required':
                setIsTyping(false);
                setMessages(prev => {
                    const updated = [...prev, {
                        type: 'approval_required',
                        confirmation: data.confirmation,
                        data: data.data,
                        timestamp: Date.now()
                    }];
                    return updated.length > MAX_MESSAGES ? updated.slice(-MAX_MESSAGES) : updated;
                });
                setStatus(null);
                break;

            default:
                console.warn("Unknown message type:", data.type);
        }
    };

    // Depend on session *presence* (!!session) not the token string.
    // This means the WebSocket only reconnects on actual login/logout,
    // not on Supabase's hourly token refresh which changes access_token.
    useEffect(() => {
        if (!session) return;

        let socket = null;
        let reconnectTimeout = null;
        let cancelled = false;

        const connectWebSocket = async () => {
            if (cancelled) return;
            try {
                const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

                // 1. Get a one-time ticket using the latest token from the ref
                const ticketResponse = await fetch(`${backendUrl}/auth/ticket`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessTokenRef.current}`
                    }
                });

                if (!ticketResponse.ok) {
                    console.error("Failed to get WebSocket ticket. Status:", ticketResponse.status);
                    if (!cancelled) reconnectTimeout = setTimeout(connectWebSocket, 5000);
                    return;
                }

                const { ticket } = await ticketResponse.json();

                if (cancelled) return;

                const apiUrl = import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8000';
                const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                const wsUrl = `${apiUrl}/ws/chat?ticket=${ticket}&timezone=${timezone}`;

                socket = new WebSocket(wsUrl);
                ws.current = socket;

                socket.onopen = () => {
                    setIsConnected(true);
                };

                socket.onclose = () => {
                    setIsConnected(false);
                    setIsTyping(false);
                    if (!cancelled) reconnectTimeout = setTimeout(connectWebSocket, 3000);
                };

                socket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    handleServerMessage(data);
                };
            } catch (error) {
                console.error("WebSocket connection error:", error);
                if (!cancelled) reconnectTimeout = setTimeout(connectWebSocket, 5000);
            }
        };

        connectWebSocket();

        return () => {
            cancelled = true;
            if (socket) {
                socket.close();
            }
            if (reconnectTimeout) {
                clearTimeout(reconnectTimeout);
            }
        };
    }, [!!session]); // eslint-disable-line react-hooks/exhaustive-deps

    const sendMessage = useCallback(async (text, stagedFiles = [], referencedFiles = [], model = null) => {
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

            setIsTyping(true);

            ws.current.send(JSON.stringify({
                type: 'message',
                sender: 'user',
                content: text,
                files: allFiles,
                timestamp: timestamp,
                ...(model && { model }),
            }));

            setStatus(null);
        } else {
            alert("Connection lost. Please wait...");
        }
    }, [session]);

    const sendApproval = useCallback((isApproved) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            setIsTyping(true);
            ws.current.send(JSON.stringify({
                type: 'approval',
                approved: isApproved
            }));
        } else {
            alert("Connection lost. Please wait...");
        }
    }, []);

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

    return {messages, setMessages, sendMessage, sendApproval, clearMessages, status, isConnected, isTyping};
};
