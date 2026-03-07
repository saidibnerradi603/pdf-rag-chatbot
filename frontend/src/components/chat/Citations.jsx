import { useState } from 'react'
import { FiChevronDown, FiChevronUp, FiBookOpen } from 'react-icons/fi'
import { motion, AnimatePresence } from 'framer-motion'

export default function Citations({ citations }) {
    const [expanded, setExpanded] = useState(false)

    if (!citations || citations.length === 0) return null

    return (
        <div>
            <button
                className="citations-toggle"
                onClick={() => setExpanded(!expanded)}
            >
                <FiBookOpen size={12} />
                {citations.length} source{citations.length !== 1 ? 's' : ''}
                {expanded ? <FiChevronUp size={12} /> : <FiChevronDown size={12} />}
            </button>

            <AnimatePresence>
                {expanded && (
                    <motion.div
                        className="citations-panel"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        {citations.map((citation, idx) => (
                            <div key={citation.id || idx} className="citation-card">
                                <div className="citation-card-header">
                                    <span className="citation-source">
                                        Source {idx + 1}
                                        {citation.metadata?.page_number &&
                                            ` · Page ${citation.metadata.page_number}`}
                                    </span>
                                    <span className="citation-score">
                                        {(citation.similarity_score * 100).toFixed(0)}% match
                                    </span>
                                </div>
                                <p className="citation-text">{citation.cited_text}</p>
                            </div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
