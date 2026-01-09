import {useState, useEffect, useRef, useCallback} from 'react';
import {supabase} from "../lib/supabase.js";

export const useChat = () => {
    const [messages, setMessages] = useState([]);
    const [status, setStatus] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef(null);
    const [session, setSession] = useState(null);
    const bucket = import.meta.env.VITE_SUPABASE_USER_FILE_BUCKET

    const handleServerMessage = (data) => {
        switch (data.type) {
            case 'history':
                console.log(data);
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
        supabase.auth.getSession().then(({data: {session}}) => {
            setSession(session);
        });

        const {
            data: {subscription},
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
            setIsConnected(true);
        };

        socket.onclose = () => {
            setIsConnected(false);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        };

        return () => socket.close();
    }, [session]);

    const sendMessage = useCallback(async (text, stagedFiles = []) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            const timestamp = Date.now();

            let uploadedFiles = [];
            if (stagedFiles.length > 0) {
                setStatus({content: "Uploading files...", icon: "📤"});
                try {
                    for (const file of stagedFiles) {
                        const fileExt = file.name.split('.').pop();
                        const fileName = `${file.name.split('.')[0]}-${Date.now()}.${fileExt}`;
                        const filePath = `${session.user.id}/${fileName}`;

                        const {data, error} = await supabase.storage.from(bucket).upload(filePath, file);

                        if (error) throw error;

                        uploadedFiles.push({
                            filename: file.name,
                            path: data.path,
                            mime_type: file.type,
                            size: file.size
                        });
                    }
                } catch (error) {
                    console.error("Error uploading files:", error);
                    alert("Failed to upload files. Please try again.");
                    setStatus(null);
                    return;
                }
            }

            setMessages(prev => [...prev, {
                type: 'message',
                sender: 'user',
                content: text,
                files: uploadedFiles,
                timestamp: timestamp
            }]);

            ws.current.send(JSON.stringify({
                type: 'message',
                sender: 'user',
                content: text,
                files: uploadedFiles,
                timestamp: timestamp
            }));
            setStatus(null);
        } else {
            alert("Connection lost. Please wait...");
        }
    }, [session, bucket]);

    return {messages, sendMessage, status, isConnected};
};