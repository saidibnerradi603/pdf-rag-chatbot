import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import EmptyState from '../ui/EmptyState'
import { HiOutlineSparkles } from 'react-icons/hi2'

export default function ChatView({
    messages,
    loading,
    streaming,
    conversationMeta,
    suggestedQuestions = [],
    onSend,
    onStop,
}) {
    const chatMessagesRef = useRef(null)

    useEffect(() => {
        const container = chatMessagesRef.current
        if (container) {
            container.scrollTop = container.scrollHeight
        }
    }, [messages])

    const handleSuggestionClick = (question) => {
        onSend(conversationMeta?.conversationId, question)
    }

    return (
        <div className="chat-view">
            <div className="chat-messages" ref={chatMessagesRef}>
                <div className="chat-messages-inner">
                    {loading ? (
                        <div className="empty-state">
                            <div className="spinner spinner-lg" />
                        </div>
                    ) : messages.length === 0 ? (
                        <div className="empty-state">
                            <div className="empty-state-icon">
                                <HiOutlineSparkles />
                            </div>
                            <h3>Start a conversation</h3>
                            <p>Ask a question about your document and get AI-powered answers with source citations.</p>
                            {suggestedQuestions.length > 0 && (
                                <div className="suggested-questions">
                                    {suggestedQuestions.map((question, idx) => (
                                        <button
                                            key={idx}
                                            className="question-chip"
                                            onClick={() => handleSuggestionClick(question)}
                                        >
                                            <HiOutlineSparkles size={14} />
                                            {question}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    ) : (
                        messages.map((msg) => (
                            <MessageBubble key={msg.id} message={msg} />
                        ))
                    )}
                </div>
            </div>

            <ChatInput
                onSend={(text) => onSend(conversationMeta?.conversationId, text)}
                onStop={onStop}
                streaming={streaming}
                disabled={loading}
            />
        </div>
    )
}
