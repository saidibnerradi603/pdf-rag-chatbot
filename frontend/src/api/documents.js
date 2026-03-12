import api from './axios'

export const documentsAPI = {
    upload: (file, onUploadProgress) => {
        const formData = new FormData()
        formData.append('file', file)
        return api.post('/documents/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress,
        })
    },

    list: (statusFilter = 'completed', limit = 50, offset = 0) =>
        api.get('/documents/', {
            params: { status_filter: statusFilter, limit, offset },
        }),

    getStatus: (documentId) => api.get(`/documents/${documentId}/status`),

    get: (documentId) => api.get(`/documents/${documentId}`),

    getDownloadUrl: (documentId, expiresIn = 3600) =>
        api.get(`/documents/${documentId}/download`, {
            params: { expires_in: expiresIn },
        }),

    delete: (documentId) => api.delete(`/documents/${documentId}`),

    process: (documentId, options = {}) =>
        api.post(`/documents/${documentId}/process`, {
            parse_options: options.parseOptions || {},
            chunk_size: options.chunkSize || 1500,
            chunk_overlap: options.chunkOverlap || 150,
        }),
}
