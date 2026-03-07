import { FiUser } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'
import MarkdownRenderer from './MarkdownRenderer'
import TypingIndicator from './TypingIndicator'
import Citations from './Citations'
import { formatTime } from '../../utils/helpers'

export default function MessageBubble({ message }) {
    const isUser = message.role === 'user'
    const isStreaming = message.isStreaming
    const isEmpty = !message.content

    return (
        <div className={`message ${message.role}`}>
            {!isUser && (
                <div className="message-avatar">
                    <HiOutlineSparkles size={16} />
                </div>
            )}

            <div className="message-content">
                <div className="message-bubble">
                    {isUser ? (
                        message.content
                    ) : isEmpty && isStreaming ? (
                        <TypingIndicator />
                    ) : (
                        <MarkdownRenderer content={message.content} />
                    )}
                </div>

                {!isUser && !isStreaming && message.citations && (
                    <Citations citations={message.citations} />
                )}

                {message.createdAt && !isStreaming && (
                    <div className="message-time">{formatTime(message.createdAt)}</div>
                )}
            </div>

            {isUser && (
                <div className="message-avatar" style={{ background: 'var(--color-primary)', color: 'var(--white)' }}>
                    <FiUser size={14} />
                </div>
            )}
        </div>
    )
}
