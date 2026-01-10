import {supabase} from "./supabase.js";
import {v4 as uuid4} from "uuid"

const bucket = import.meta.env.VITE_SUPABASE_USER_FILE_BUCKET;

export const downloadFile = async (file) => {
    const {data, error} = await supabase.storage.from(bucket).download(file.path);

    if (error) throw error;

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

export const uploadFiles = async (user_id, files) => {
    if (files.length === 0) return;
    const uploadedFiles = [];
    for (const file of files) {
        const id = uuid4();
        const filePath = `${user_id}/${file.name} ** ${id}`;
        const {data, error} = await supabase.storage.from(bucket).upload(filePath, file);
        if (error) throw error;
        uploadedFiles.push({
            id: id,
            filename: file.name,
            path: filePath,
            mime_type: file.type,
            size: file.size
        });
    }
    return uploadedFiles;
}

export const deleteFile = async (file) => {
    const {error} = await supabase.storage
        .from(bucket)
        .remove([file.path]);

    if (error) throw error;
}

export const listFiles = async (user_id) => {
    const files = []
    const {data, error} = await supabase.storage.from(bucket).list(user_id, {sortBy: {column: 'name', order: 'asc'}});
    console.log(data)
    if (error) {
        throw error;
    }
    if (data) {
        for (const file of data) {
            files.push({
                'id': file.name.split(' ** ')[1],
                'filename': file.name.split(' ** ')[0],
                'path': `${user_id}/${file.name}`,
                'mime_type': file.metadata?.mimetype,
                'size': file.metadata?.size,
            });
        }
    }
    return files;
}

export const bytesToSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};