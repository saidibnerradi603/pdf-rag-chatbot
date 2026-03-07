import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { HiOutlineCloudArrowUp } from 'react-icons/hi2'
import { motion, AnimatePresence } from 'framer-motion'

export default function UploadZone({ onUpload }) {
    const [uploadProgress, setUploadProgress] = useState(null)
    const [uploading, setUploading] = useState(false)

    const onDrop = useCallback(
        async (acceptedFiles) => {
            if (acceptedFiles.length === 0) return
            const file = acceptedFiles[0]

            setUploading(true)
            setUploadProgress(0)

            try {
                await onUpload(file, (pct) => setUploadProgress(pct))
            } finally {
                setUploading(false)
                setUploadProgress(null)
            }
        },
        [onUpload]
    )

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        maxSize: 5 * 1024 * 1024,
        maxFiles: 1,
        disabled: uploading,
    })

    return (
        <div
            {...getRootProps()}
            className={`upload-zone ${isDragActive ? 'drag-active' : ''}`}
        >
            <input {...getInputProps()} />
            <div className="upload-zone-icon">
                <HiOutlineCloudArrowUp />
            </div>

            <AnimatePresence mode="wait">
                {uploading ? (
                    <motion.div
                        key="uploading"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <h3>Uploading...</h3>
                        <div className="upload-progress">
                            <div className="progress-bar">
                                <div
                                    className="progress-bar-fill"
                                    style={{ width: `${uploadProgress || 0}%` }}
                                />
                            </div>
                            <p className="upload-progress-text">{uploadProgress}%</p>
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        key="idle"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <h3>
                            {isDragActive ? 'Drop your PDF here' : 'Upload a PDF document'}
                        </h3>
                        <p>Drag & drop or click to browse · PDF only · Max 5 MB</p>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
