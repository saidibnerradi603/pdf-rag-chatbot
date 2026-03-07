import { useState } from 'react'
import { FiPlus, FiMessageSquare, FiTrash2, FiLogOut } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'
import { useAuth } from '../../context/AuthContext'
import { getInitials, truncate } from '../../utils/helpers'
import ConfirmDialog from '../ui/ConfirmDialog'
import { motion, AnimatePresence } from 'framer-motion'

export default function Sidebar({
    conversations,
    conversationsLoading,
    activeConversationId,
    onSelectConversation,
    onNewChat,
    onDeleteConversation,
}) {
    const { user, logout } = useAuth()
    const [deleteTarget, setDeleteTarget] = useState(null)

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-brand">
                    <span className="sidebar-brand-icon">
                        <HiOutlineSparkles size={16} />
                    </span>
                    PDF RAG Chat
                </div>
                <button className="new-chat-btn" onClick={onNewChat}>
                    <FiPlus size={16} />
                    New Chat
                </button>
            </div>

            <div className="sidebar-section">
                {conversationsLoading ? (
                    <div className="sidebar-loading">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="conversation-item-skeleton">
                                <div className="skeleton-line" />
                            </div>
                        ))}
                    </div>
                ) : conversations.length > 0 ? (
                    <>
                        <div className="sidebar-section-title">Conversations</div>
                        <AnimatePresence>
                            {conversations.map((conv) => (
                                <motion.div
                                    key={conv.id}
                                    className={`conversation-item ${conv.id === activeConversationId ? 'active' : ''
                                        }`}
                                    onClick={() => onSelectConversation(conv.id)}
                                    layout
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -10 }}
                                    transition={{ duration: 0.2 }}
                                >
                                    <FiMessageSquare className="conversation-item-icon" size={15} />
                                    <span className="conversation-item-text">
                                        {truncate(conv.title, 28)}
                                    </span>
                                    <button
                                        className="conversation-item-delete"
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            setDeleteTarget(conv)
                                        }}
                                        title="Delete"
                                    >
                                        <FiTrash2 size={14} />
                                    </button>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </>
                ) : null}
            </div>

            <div className="sidebar-footer">
                <div className="user-menu">
                    <div className="user-avatar">{getInitials(user?.email)}</div>
                    <div className="user-info">
                        <div className="user-email">{user?.email}</div>
                    </div>
                    <button className="logout-btn" onClick={logout} title="Logout">
                        <FiLogOut size={16} />
                    </button>
                </div>
            </div>

            <ConfirmDialog
                open={!!deleteTarget}
                title="Delete conversation?"
                description="This will permanently delete this conversation and all its messages and citations."
                confirmLabel="Delete"
                danger
                onConfirm={() => {
                    onDeleteConversation(deleteTarget.id)
                    setDeleteTarget(null)
                }}
                onCancel={() => setDeleteTarget(null)}
            />
        </aside>
    )
}
