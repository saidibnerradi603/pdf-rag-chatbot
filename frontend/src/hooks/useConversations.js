import { useState, useCallback, useEffect } from 'react'
import { conversationsAPI } from '../api/conversations'
import { getErrorMessage } from '../utils/helpers'
import toast from 'react-hot-toast'

export function useConversations() {
    const [conversations, setConversations] = useState([])
    const [loading, setLoading] = useState(true)

    const fetchConversations = useCallback(async () => {
        setLoading(true)
        try {
            const res = await conversationsAPI.list()
            setConversations(res.data)
        } catch (err) {
            toast.error(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchConversations()
    }, [fetchConversations])

    const createConversation = useCallback(async (documentId) => {
        const res = await conversationsAPI.create(documentId)
        const newConv = res.data
        setConversations((prev) => [newConv, ...prev])
        return newConv
    }, [])

    const deleteConversation = useCallback(async (conversationId) => {
        await conversationsAPI.delete(conversationId)
        setConversations((prev) => prev.filter((c) => c.id !== conversationId))
        toast.success('Conversation deleted')
    }, [])

    const updateConversationTitle = useCallback((conversationId, newTitle) => {
        setConversations((prev) =>
            prev.map((c) =>
                c.id === conversationId ? { ...c, title: newTitle } : c
            )
        )
    }, [])

    return {
        conversations,
        loading,
        fetchConversations,
        createConversation,
        deleteConversation,
        updateConversationTitle,
    }
}
