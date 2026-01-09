import { useState, useEffect, useRef, useCallback } from 'react';
import {supabase} from "../lib/supabase.js";

export const useChat = () => {
    const [messages, setMessages] = useState([]);
    const [status, setStatus] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef(null);
    const [session, setSession] = useState(null);

    const handleServerMessage = (data) => {
        switch (data.type) {
            case 'history':
                console.log(data);
                setMessages(data.messages)
                break;

            case 'message':
                setMessages(messages => [...messages, { 
                    sender: data.sender, 
                    content: data.content, 
                    files: data.files,
                    timestamp: data.timestamp 
                }]);
                break;

            case 'status':
                setStatus({ content: data.content, icon: data.icon });
                break;

            case 'error':
                if (data.code === 'AUTH_REQUIRED') {
                    console.error("Auth required:", data.content);
                    // You might want to trigger a logout or redirect here
                    alert(`Authentication Session Expired: ${data.content}`);
                } else {
                    alert(`Error: ${data.content}`);
                }
                break;

            default:
                console.warn("Unknown message type:", data.type);
        }
    };

    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
        });

        const {
            data: { subscription },
        } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
        });

        return () => subscription.unsubscribe();
    }, []);

    useEffect(() => {
        if (!session?.access_token) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
        const wsUrl = `http://localhost:8000/ws/chat?token=${session.access_token}&timezone=${timezone}`;

        const socket = new WebSocket(wsUrl);
        ws.current = socket;

        socket.onopen = () => {
            console.log("✅ Connected to Agent");
            setIsConnected(true);
        };

        socket.onclose = () => {
            console.log("❌ Disconnected");
            setIsConnected(false);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        };

        return () => socket.close();
    }, [session]);

    const sendMessage = useCallback((text, fileData = null) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            const timestamp = Date.now();
            setMessages(prev => [...prev, {
                type: 'message',
                sender: 'user', 
                content: text, 
                files: [], // Optimistic update assumes no files for now unless handled
                timestamp: timestamp 
            }]);

            ws.current.send(JSON.stringify({
                type: 'message',
                sender: 'user',
                content: text,
                files: [],
                timestamp: timestamp
            }));
        } else {
            alert("Connection lost. Please wait...");
        }
    }, []);

    return { messages, sendMessage, status, isConnected };
};