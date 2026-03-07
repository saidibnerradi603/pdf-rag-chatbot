import { motion } from 'framer-motion'

export default function ConfirmDialog({ open, title, description, confirmLabel, onConfirm, onCancel, danger }) {
    if (!open) return null

    return (
        <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCancel}
        >
            <motion.div
                className="modal-content"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2 }}
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="modal-title">{title}</h3>
                <p className="modal-description">{description}</p>
                <div className="modal-actions">
                    <button className="btn btn-secondary" onClick={onCancel}>
                        Cancel
                    </button>
                    <button
                        className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`}
                        onClick={onConfirm}
                    >
                        {confirmLabel || 'Confirm'}
                    </button>
                </div>
            </motion.div>
        </motion.div>
    )
}
