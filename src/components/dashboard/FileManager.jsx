import {useState, useRef} from 'react';
import {FileText, Trash2, Upload, Image, Film, Music} from 'lucide-react';

export default function FileManager() {
    const [files, setFiles] = useState([
        {id: 1, name: 'project_proposal.pdf', type: 'pdf', size: '2.4 MB', date: '2023-10-24'},
        {id: 2, name: 'data_analysis.csv', type: 'csv', size: '156 KB', date: '2023-10-23'},
        {id: 3, name: 'avatar.png', type: 'image', size: '4.2 MB', date: '2023-10-20'},
    ]);
    const fileInputRef = useRef(null);

    const handleDelete = (id) => {
        setFiles(files.filter(f => f.id !== id));
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e) => {
        const filesList = Array.from(e.target.files || []);
        if (filesList.length === 0) return;

        const newFiles = filesList.map((file, index) => ({
            id: Date.now() + index,
            name: file.name,
            type: file.type.split('/')[0] || 'unknown',
            size: (file.size / 1024 / 1024).toFixed(2) + ' MB',
            date: new Date().toISOString().split('T')[0]
        }));

        setFiles(prev => [...newFiles, ...prev]);
        e.target.value = null; // Reset input
    };

    const getIcon = (type, size = 48) => {
        if (type === 'image') return <Image size={size} className="text-purple-500"/>;
        if (type === 'video') return <Film size={size} className="text-red-500"/>;
        if (type === 'audio') return <Music size={size} className="text-yellow-500"/>;
        return <FileText size={size} className="text-blue-500"/>;
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Files</h2>
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
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                        <Upload size={18}/>
                        <span>Upload File</span>
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {files.map((file) => (
                    <div
                        key={file.id}
                        className="group relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-6 flex flex-col items-center justify-center gap-4 hover:shadow-md transition-shadow aspect-square"
                    >
                        <div className="p-4 bg-zinc-50 dark:bg-zinc-800 rounded-full">
                            {getIcon(file.type)}
                        </div>

                        <div className="text-center w-full px-2">
                            <p className="font-medium text-zinc-900 dark:text-zinc-100 text-sm break-words line-clamp-2"
                               title={file.name}>
                                {file.name}
                            </p>
                            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                                {file.size}
                            </p>
                        </div>

                        <button
                            onClick={() => handleDelete(file.id)}
                            className="absolute top-2 right-2 p-1.5 text-red-500 bg-red-50 dark:bg-red-900/20 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
                            title="Delete file"
                        >
                            <Trash2 size={16}/>
                        </button>
                    </div>
                ))}

                {files.length === 0 && (
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