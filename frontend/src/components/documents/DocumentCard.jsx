import { useState } from 'react'
import { FiFileText, FiTrash2, FiDownload, FiPlay, FiMessageSquare } from 'react-icons/fi'
import { motion } from 'framer-motion'
import StatusBadge from './StatusBadge'
import ConfirmDialog from '../ui/ConfirmDialog'
import { useProcessing } from '../../hooks/useProcessing'
import { formatDate, formatFileSize, getErrorMessage } from '../../utils/helpers'
import toast from 'react-hot-toast'

export default function DocumentCard({
    document,
    onDelete,
    onDownload,
    onProcess,
    onChat,
    onStatusChange,
}) {
    const [confirmDelete, setConfirmDelete] = useState(false)
    const [processing, setProcessing] = useState(false)
    const { status, polling, startPolling } = useProcessing(
        document.id,
        document.status,
        onStatusChange
    )

    const currentStatus = polling ? status : document.status
    const isReady = currentStatus === 'completed'
    const isProcessing = currentStatus === 'processing'
    const isPending = currentStatus === 'pending'
    const isFailed = currentStatus === 'failed'

    async function handleProcess() {
        setProcessing(true)
        try {
            await onProcess(document.id)
            startPolling()
        } catch (err) {
            toast.error(getErrorMessage(err))
            startPolling()
        } finally {
            setProcessing(false)
        }
    }

    async function handleDownload() {
        try {
            const url = await onDownload(document.id)
            window.open(url, '_blank')
        } catch (err) {
            toast.error(getErrorMessage(err))
        }
    }

    return (
        <>
            <motion.div
                className="document-card"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                layout
            >
                <div className="document-icon">
                    <FiFileText />
                </div>

                <div className="document-info">
                    <div className="document-name">{document.file_name}</div>
                    <div className="document-meta">
                        <span>{formatDate(document.created_at)}</span>
                        {document.metadata?.file_size && (
                            <>
                                <span>·</span>
                                <span>{formatFileSize(document.metadata.file_size)}</span>
                            </>
                        )}
                    </div>
                </div>

                <StatusBadge status={currentStatus} />

                <div className="document-actions">
                    {(isPending || isFailed) && (
                        <button
                            className="btn btn-sm btn-secondary"
                            onClick={handleProcess}
                            disabled={processing || isProcessing}
                            title="Process document"
                        >
                            {processing || isProcessing ? (
                                <span className="spinner spinner-sm" />
                            ) : (
                                <>
                                    <FiPlay size={14} /> Process
                                </>
                            )}
                        </button>
                    )}

                    {isReady && (
                        <button
                            className="btn btn-sm btn-primary"
                            onClick={() => onChat(document)}
                            title="Start chat"
                        >
                            <FiMessageSquare size={14} /> Chat
                        </button>
                    )}

                    <button
                        className="btn-icon"
                        onClick={handleDownload}
                        title="Download"
                    >
                        <FiDownload size={16} />
                    </button>

                    <button
                        className="btn-icon"
                        onClick={() => setConfirmDelete(true)}
                        title="Delete"
                    >
                        <FiTrash2 size={16} />
                    </button>
                </div>
            </motion.div>

            <ConfirmDialog
                open={confirmDelete}
                title="Delete document?"
                description="This will permanently delete the document and all associated data including chunks, conversations, messages, and citations."
                confirmLabel="Delete"
                danger
                onConfirm={() => {
                    setConfirmDelete(false)
                    onDelete(document.id)
                }}
                onCancel={() => setConfirmDelete(false)}
            />
        </>
    )
}
