import api from './axios'

export const conversationsAPI = {
    create: (documentId, title) => {
        const body = { document_id: documentId }
        if (title) body.title = title
        return api.post('/conversations/', body)
    },

    list: () => api.get('/conversations/'),

    getHistory: (conversationId) =>
        api.get(`/conversations/${conversationId}/history`),

    delete: (conversationId) =>
        api.delete(`/conversations/${conversationId}`),
}
