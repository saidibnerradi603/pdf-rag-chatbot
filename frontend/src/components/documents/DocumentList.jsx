import { AnimatePresence } from 'framer-motion'
import DocumentCard from './DocumentCard'
import EmptyState from '../ui/EmptyState'
import { FiFileText } from 'react-icons/fi'

const FILTERS = ['completed', 'pending', 'processing', 'failed']

export default function DocumentList({
    documents,
    loading,
    statusFilter,
    onFilterChange,
    onDelete,
    onDownload,
    onProcess,
    onChat,
    onStatusChange,
}) {
    return (
        <div>
            <div className="document-list-header">
                <h2>Your Documents</h2>
                <div className="status-filter">
                    {FILTERS.map((f) => (
                        <button
                            key={f}
                            className={`status-filter-btn ${statusFilter === f ? 'active' : ''}`}
                            onClick={() => onFilterChange(f)}
                        >
                            {f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className="empty-state">
                    <div className="spinner spinner-lg" />
                </div>
            ) : documents.length === 0 ? (
                <EmptyState
                    icon={<FiFileText />}
                    title="No documents"
                    description={`No ${statusFilter} documents found. Upload a PDF to get started.`}
                />
            ) : (
                <div className="document-list">
                    <AnimatePresence>
                        {documents.map((doc) => (
                            <DocumentCard
                                key={doc.id}
                                document={doc}
                                onDelete={onDelete}
                                onDownload={onDownload}
                                onProcess={onProcess}
                                onChat={onChat}
                                onStatusChange={onStatusChange}
                            />
                        ))}
                    </AnimatePresence>
                </div>
            )}
        </div>
    )
}
