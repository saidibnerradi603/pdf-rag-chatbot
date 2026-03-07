import { useState, useCallback } from 'react'
import Sidebar from '../components/layout/Sidebar'
import ChatView from '../components/chat/ChatView'
import UploadZone from '../components/documents/UploadZone'
import DocumentList from '../components/documents/DocumentList'
import EmptyState from '../components/ui/EmptyState'
import { useDocuments } from '../hooks/useDocuments'
import { useConversations } from '../hooks/useConversations'
import { useChat } from '../hooks/useChat'
import { getErrorMessage } from '../utils/helpers'
import toast from 'react-hot-toast'
import { FiFileText, FiMessageSquare, FiX } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'
import { motion, AnimatePresence } from 'framer-motion'

export default function DashboardPage() {
    const [activeView, setActiveView] = useState('documents')
    const [activeConversationId, setActiveConversationId] = useState(null)
    const [showNewChatModal, setShowNewChatModal] = useState(false)
    const [completedDocs, setCompletedDocs] = useState([])
    const [loadingDocs, setLoadingDocs] = useState(false)

    const {
        documents,
        loading: docsLoading,
        statusFilter,
        changeFilter,
        fetchDocuments,
        uploadDocument,
        processDocument,
        deleteDocument,
        getDownloadUrl,
    } = useDocuments('completed')

    const {
        conversations,
        loading: conversationsLoading,
        fetchConversations,
        createConversation,
        deleteConversation,
        updateConversationTitle,
    } = useConversations()

    const {
        messages,
        conversationMeta,
        loading: chatLoading,
        streaming,
        loadHistory,
        sendMessage,
        stopStreaming,
        clearChat,
    } = useChat({
        onTitleUpdate: updateConversationTitle,
    })

    const loadCompletedDocs = useCallback(async () => {
        setLoadingDocs(true)
        try {
            const { documentsAPI } = await import('../api/documents')
            const res = await documentsAPI.list('completed')
            setCompletedDocs(res.data)
        } catch {
            // ignore
        } finally {
            setLoadingDocs(false)
        }
    }, [])

    const startChatWithDocument = useCallback(
        async (doc) => {
            try {
                const conv = await createConversation(doc.id)
                setActiveConversationId(conv.id)
                setActiveView('chat')
                await loadHistory(conv.id)
            } catch (err) {
                toast.error(getErrorMessage(err))
            }
        },
        [createConversation, loadHistory]
    )

    const handleSelectConversation = useCallback(
        async (conversationId) => {
            setActiveConversationId(conversationId)
            setActiveView('chat')
            await loadHistory(conversationId)
        },
        [loadHistory]
    )

    const handleNewChat = useCallback(() => {
        loadCompletedDocs()
        setShowNewChatModal(true)
    }, [loadCompletedDocs])

    const handleCreateConversation = useCallback(
        async (doc) => {
            setShowNewChatModal(false)
            await startChatWithDocument(doc)
        },
        [startChatWithDocument]
    )

    const handleDeleteConversation = useCallback(
        async (conversationId) => {
            await deleteConversation(conversationId)
            if (activeConversationId === conversationId) {
                clearChat()
                setActiveConversationId(null)
                setActiveView('documents')
            }
        },
        [deleteConversation, activeConversationId, clearChat]
    )

    const handleDeleteDocument = useCallback(
        async (documentId) => {
            await deleteDocument(documentId)
            fetchConversations()
            if (conversationMeta?.documentId === documentId) {
                clearChat()
                setActiveConversationId(null)
                setActiveView('documents')
            }
        },
        [deleteDocument, fetchConversations, conversationMeta, clearChat]
    )

    const handleUpload = useCallback(
        async (file, onProgress) => {
            try {
                const result = await uploadDocument(file, onProgress)
                toast.success(`"${result.file_name}" uploaded successfully`)
                changeFilter('pending')
                fetchDocuments('pending')
            } catch (err) {
                toast.error(getErrorMessage(err))
                throw err
            }
        },
        [uploadDocument, changeFilter, fetchDocuments]
    )

    const handleProcess = useCallback(
        async (documentId) => {
            await processDocument(documentId)
            toast.success('Processing started')
        },
        [processDocument]
    )

    const handleDocumentStatusChange = useCallback(
        (documentId, newStatus) => {
            if (newStatus === 'completed') {
                toast.success('Document processed successfully!')
                changeFilter('completed')
            } else if (newStatus === 'failed') {
                toast.error('Document processing failed')
                changeFilter('failed')
            }
        },
        [changeFilter]
    )

    const handleBackToDocuments = useCallback(() => {
        setActiveView('documents')
        setActiveConversationId(null)
        clearChat()
    }, [clearChat])

    return (
        <div className="dashboard">
            <Sidebar
                conversations={conversations}
                conversationsLoading={conversationsLoading}
                activeConversationId={activeConversationId}
                onSelectConversation={handleSelectConversation}
                onNewChat={handleNewChat}
                onDeleteConversation={handleDeleteConversation}
            />

            <div className="main-content">
                <div className="header">
                    <div className="header-title">
                        {activeView === 'chat' && conversationMeta
                            ? conversationMeta.title || 'Chat'
                            : 'Documents'}
                    </div>
                    <div className="header-actions">
                        {activeView === 'chat' && (
                            <button
                                className="btn btn-sm btn-secondary"
                                onClick={handleBackToDocuments}
                            >
                                <FiFileText size={14} /> Documents
                            </button>
                        )}
                    </div>
                </div>

                {activeView === 'documents' ? (
                    <div className="documents-view">
                        <h1 className="documents-title">Documents</h1>
                        <p className="documents-subtitle">
                            Upload PDFs to analyze them with AI-powered Q&A
                        </p>
                        <UploadZone onUpload={handleUpload} />
                        <DocumentList
                            documents={documents}
                            loading={docsLoading}
                            statusFilter={statusFilter}
                            onFilterChange={changeFilter}
                            onDelete={handleDeleteDocument}
                            onDownload={getDownloadUrl}
                            onProcess={handleProcess}
                            onChat={startChatWithDocument}
                            onStatusChange={handleDocumentStatusChange}
                        />
                    </div>
                ) : (
                    <ChatView
                        messages={messages}
                        loading={chatLoading}
                        streaming={streaming}
                        conversationMeta={conversationMeta}
                        onSend={sendMessage}
                        onStop={stopStreaming}
                    />
                )}
            </div>

            <AnimatePresence>
                {showNewChatModal && (
                    <motion.div
                        className="modal-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setShowNewChatModal(false)}
                    >
                        <motion.div
                            className="modal-content"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            transition={{ duration: 0.2 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex items-center justify-between mb-md">
                                <h3 className="modal-title" style={{ margin: 0 }}>
                                    Select a document
                                </h3>
                                <button
                                    className="btn-icon"
                                    onClick={() => setShowNewChatModal(false)}
                                >
                                    <FiX size={18} />
                                </button>
                            </div>
                            <p className="text-sm text-muted" style={{ marginBottom: 'var(--space-md)' }}>
                                Choose a processed document to start chatting with
                            </p>

                            {loadingDocs ? (
                                <div className="empty-state" style={{ padding: 'var(--space-xl)' }}>
                                    <div className="spinner spinner-md" />
                                </div>
                            ) : completedDocs.length === 0 ? (
                                <EmptyState
                                    icon={<FiFileText />}
                                    title="No documents ready"
                                    description="Upload and process a PDF document first."
                                />
                            ) : (
                                <div className="doc-selector-list">
                                    {completedDocs.map((doc) => (
                                        <button
                                            key={doc.id}
                                            className="doc-selector-item"
                                            onClick={() => handleCreateConversation(doc)}
                                        >
                                            <div className="document-icon" style={{ width: 32, height: 32, fontSize: 'var(--font-size-md)' }}>
                                                <FiFileText />
                                            </div>
                                            <div className="document-info">
                                                <div className="document-name">{doc.file_name}</div>
                                                <div className="document-meta">
                                                    {doc.metadata?.file_size}
                                                </div>
                                            </div>
                                            <FiMessageSquare
                                                size={16}
                                                style={{ color: 'var(--color-text-muted)' }}
                                            />
                                        </button>
                                    ))}
                                </div>
                            )}
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
