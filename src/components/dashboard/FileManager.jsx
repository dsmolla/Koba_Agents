import {useState, useRef, useEffect} from 'react';
import {FileText, Trash2, Upload, Image, Film, Music, Loader2} from 'lucide-react';
import {getCurrentUser, supabase} from "../../lib/supabase.js";

export default function FileManager() {
    const [files, setFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [user, setUser] = useState(null);
    const fileInputRef = useRef(null);
    const bucket = import.meta.env.VITE_SUPABASE_USER_FILE_BUCKET

    useEffect(() => {
        getCurrentUser().then((user) => {
            setUser(user);

            const files = []
            supabase.storage.from(bucket).list(
                user.id,
                {
                    limit: 100,
                    offset: 0,
                    sortBy: { column: 'name', order: 'asc' },
                }).then(({data, error}) => {
                    // console.log(data)
                    for (const file of data) {
                        console.log(file)
                        files.push({
                            'filename': file.name,
                            'path': `${user.id}/${file.name}`,
                            'mime_type': file.metadata?.mimetype,
                            'size': file.metadata?.size,
                        });
                    }
                    setFiles(files);
            })
        })
        
    }, []);

    const bytesToSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const handleDelete = async (file) => {
        if (!user) return;
        
        try {
            const { error } = await supabase.storage
                .from(bucket)
                .remove([file.path]);
            
            if (error) throw error;
            setFiles(files.filter(f => f.id !== file.id));
        } catch (error) {
            console.error("Error deleting file:", error);
            alert("Failed to delete file.");
        }
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (e) => {
        const filesList = Array.from(e.target.files || []);
        if (filesList.length === 0 || !user) return;

        setIsUploading(true);
        const uploadedFiles = [];

        try {
            for (const file of filesList) {
                const filePath = `${user.id}/${file.name}`;

                const { data, error } = await supabase.storage
                    .from(bucket)
                    .upload(filePath, file);

                if (error) throw error;

                uploadedFiles.push({
                    filename: file.name,
                    path: filePath,
                    mime_type: file.type,
                    size: file.size
                });
            }
            setFiles(prev => [...uploadedFiles, ...prev]);
        } catch (error) {
            console.error("Error uploading files:", error);
            alert("Failed to upload files.");
        } finally {
            setIsUploading(false);
            e.target.value = null; // Reset input
        }
    };

    const downloadFile = async (file) => {
        const {data, error} = await supabase.storage.from(bucket).download(file.path);
        if (data) {
            const url = URL.createObjectURL(data)
            const a = document.createElement('a')
            a.href = url
            a.download = file.filename
            document.body.appendChild(a)
            a.click()

            document.body.removeChild(a)
            URL.revokeObjectURL(url)
        }
    }

    const getIcon = (type, size = 48) => {
        if (type === 'image') return <Image size={size} className="text-purple-500"/>;
        if (type === 'video') return <Film size={size} className="text-red-500"/>;
        if (type === 'audio') return <Music size={size} className="text-yellow-500"/>;
        return <FileText size={size} className="text-blue-500"/>;
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-white">Files</h2>
                <div>
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        multiple
                        onChange={handleFileChange}
                    />
                    <button
                        onClick={handleUploadClick}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                    >
                        <Upload size={18}/>
                        <span>Upload File</span>
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {files.map((file) => (
                    <div
                        key={file.filename}
                        className="group relative bg-secondary-dark-bg border border-dark-border rounded-lg p-6 flex flex-col items-center justify-center gap-4 hover:shadow-md hover:bg-primary-800 hover:cursor-pointer transition-shadow aspect-square"
                        onClick={() => downloadFile(file)}
                    >
                        <div className="p-4 bg-gray-700 rounded-full">
                            {getIcon(file.mime_type.split('/')[0])}
                        </div>

                        <div className="text-center w-full px-2">
                            <p className="font-medium text-white text-sm wrap-break-word line-clamp-2"
                               title={file.filename}>
                                {file.filename}
                            </p>
                            <p className="text-xs text-gray-300 mt-1">
                                {bytesToSize(file.size)}
                            </p>
                        </div>

                        <button
                            onClick={() => handleDelete(file)}
                            className="absolute top-2 right-2 p-1.5 text-red-500 bg-red-900/70 hover:bg-red-900/85 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
                            title="Delete file"
                        >
                            <Trash2 size={16}/>
                        </button>
                    </div>
                ))}

                {isUploading && (
                    <div className="bg-secondary-dark-bg border border-dark-border rounded-lg p-6 flex flex-col items-center justify-center gap-4 aspect-square">
                        <Loader2 size={48} className="text-blue-500 animate-spin"/>
                        <p className="text-xs text-gray-300">Uploading...</p>
                    </div>
                )}

                {files.length === 0 && !isUploading && (
                    <div
                        className="col-span-full py-12 flex flex-col items-center justify-center text-zinc-400 border-2 border-dashed border-zinc-200 dark:border-zinc-800 rounded-lg">
                        <Upload size={48} className="mb-4 opacity-50"/>
                        <p className="text-lg font-medium">No files uploaded</p>
                        <p className="text-sm">Upload files to see them here</p>
                    </div>
                )}
            </div>
        </div>
    );
}