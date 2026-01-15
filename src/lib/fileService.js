import {supabase} from "./supabase.js";
import {customAlphabet} from "nanoid";

const bucket = import.meta.env.VITE_SUPABASE_USER_FILE_BUCKET;
const generateShortID = customAlphabet('1234567890abcdefghijklmnopqrstuvwxyz', 4)

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
        const short_id = generateShortID();
        const lastDotIndex = file.name.lastIndexOf('.');
        let filename = ''
        if (lastDotIndex === -1) {
            filename = `${file.name}_${short_id}`
        } else {
            const name = file.name.substring(0, lastDotIndex)
            const ext = file.name.substring(lastDotIndex)
            filename = `${name}_${short_id}${ext}`
        }
        const filePath = `${user_id}/${filename}`;
        const {data, error} = await supabase.storage.from(bucket).upload(filePath, file);
        if (error) throw error;
        uploadedFiles.push({
            filename: filename,
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
                'filename': file.name,
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