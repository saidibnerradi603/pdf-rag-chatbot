import { useState, useRef, useEffect } from 'react'
import { FiSend, FiSquare } from 'react-icons/fi'

export default function ChatInput({ onSend, onStop, streaming, disabled }) {
    const [message, setMessage] = useState('')
    const textareaRef = useRef(null)

    const charCount = message.length
    const maxChars = 2000
    const canSend = message.trim().length > 0 && !streaming && !disabled && charCount <= maxChars

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto'
            textareaRef.current.style.height =
                Math.min(textareaRef.current.scrollHeight, 150) + 'px'
        }
    }, [message])

    function handleSubmit(e) {
        e?.preventDefault()
        if (!canSend) return
        onSend(message.trim())
        setMessage('')
    }

    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSubmit()
        }
    }

    return (
        <div className="chat-input-area">
            <form className="chat-input-container" onSubmit={handleSubmit}>
                <div className="chat-input-wrapper">
                    <textarea
                        ref={textareaRef}
                        className="chat-input"
                        rows={1}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask a question about your document..."
                        disabled={disabled}
                        maxLength={maxChars}
                    />
                    {charCount > 1500 && (
                        <span
                            className={`char-count ${charCount > 1900 ? 'at-limit' : charCount > 1500 ? 'near-limit' : ''
                                }`}
                        >
                            {charCount}/{maxChars}
                        </span>
                    )}
                </div>

                {streaming ? (
                    <button
                        type="button"
                        className="send-btn"
                        onClick={onStop}
                        title="Stop generating"
                        style={{ background: 'var(--color-error)' }}
                    >
                        <FiSquare size={18} />
                    </button>
                ) : (
                    <button
                        type="submit"
                        className="send-btn"
                        disabled={!canSend}
                        title="Send message"
                    >
                        <FiSend size={18} />
                    </button>
                )}
            </form>
        </div>
    )
}
