import { useState, useCallback, useRef } from 'react'
import { conversationsAPI } from '../api/conversations'
import { documentsAPI } from '../api/documents'
import { streamChat } from '../api/stream'
import { getErrorMessage } from '../utils/helpers'
import toast from 'react-hot-toast'

export function useChat({ onTitleUpdate } = {}) {
    const [messages, setMessages] = useState([])
    const [conversationMeta, setConversationMeta] = useState(null)
    const [loading, setLoading] = useState(false)
    const [streaming, setStreaming] = useState(false)
    const [suggestedQuestions, setSuggestedQuestions] = useState([])
    const abortControllerRef = useRef(null)

    const loadHistory = useCallback(async (conversationId) => {
        setLoading(true)
        setSuggestedQuestions([])
        try {
            const res = await conversationsAPI.getHistory(conversationId)
            const data = res.data
            setConversationMeta({
                conversationId: data.conversation_id,
                documentId: data.document_id,
                title: data.title,
            })
            setMessages(
                data.messages.map((m) => ({
                    id: m.id,
                    role: m.role,
                    content: m.content,
                    createdAt: m.created_at,
                    citations: m.citations || null,
                }))
            )

            if (data.messages.length === 0 && data.document_id) {
                try {
                    const docRes = await documentsAPI.get(data.document_id)
                    if (docRes.data.suggested_questions?.length > 0) {
                        setSuggestedQuestions(docRes.data.suggested_questions)
                    }
                } catch {
                    // ignore
                }
            }
        } catch (err) {
            toast.error(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }, [])

    const clearChat = useCallback(() => {
        setMessages([])
        setConversationMeta(null)
        setStreaming(false)
        setSuggestedQuestions([])
    }, [])

    const sendMessage = useCallback(
        async (conversationId, message, options = {}) => {
            const isFirstMessage = messages.filter((m) => m.role === 'user').length === 0

            setSuggestedQuestions([])

            const userMsg = {
                id: `temp-user-${Date.now()}`,
                role: 'user',
                content: message,
                createdAt: new Date().toISOString(),
            }
            setMessages((prev) => [...prev, userMsg])

            const assistantId = `temp-ai-${Date.now()}`
            setMessages((prev) => [
                ...prev,
                {
                    id: assistantId,
                    role: 'assistant',
                    content: '',
                    createdAt: new Date().toISOString(),
                    citations: null,
                    isStreaming: true,
                },
            ])

            setStreaming(true)

            const controller = new AbortController()
            abortControllerRef.current = controller

            await streamChat(conversationId, message, options, {
                onToken: (token) => {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId
                                ? { ...m, content: m.content + token }
                                : m
                        )
                    )
                },
                onMetadata: (metadata) => {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId
                                ? {
                                    ...m,
                                    id: metadata.message_id || m.id,
                                    citations: metadata.citations || [],
                                    isStreaming: false,
                                }
                                : m
                        )
                    )
                },
                onDone: () => {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId ? { ...m, isStreaming: false } : m
                        )
                    )
                    setStreaming(false)

                    if (isFirstMessage) {
                        const newTitle = message.length > 50
                            ? message.slice(0, 50) + '...'
                            : message                      
                        setConversationMeta((prev) =>
                            prev ? { ...prev, title: newTitle } : prev
                        )           
                        onTitleUpdate?.(conversationId, newTitle)
                    }
                },
                onError: (error) => {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === assistantId
                                ? {
                                    ...m,
                                    content: m.content || 'Sorry, an error occurred while generating the response.',
                                    isStreaming: false,
                                    isError: true,
                                }
                                : m
                        )
                    )
                    setStreaming(false)
                    toast.error(getErrorMessage(error))
                },
                signal: controller.signal,
            })
        },
        [messages, onTitleUpdate]
    )

    const stopStreaming = useCallback(() => {
        abortControllerRef.current?.abort()
        setStreaming(false)
        setMessages((prev) =>
            prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m))
        )
    }, [])

    return {
        messages,
        conversationMeta,
        loading,
        streaming,
        suggestedQuestions,
        loadHistory,
        sendMessage,
        stopStreaming,
        clearChat,
    }
}
