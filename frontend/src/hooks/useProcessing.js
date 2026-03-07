import { useState, useEffect, useRef, useCallback } from 'react'
import { documentsAPI } from '../api/documents'

const POLL_INTERVAL = 3000

export function useProcessing(documentId, initialStatus, onStatusChange) {
    const [status, setStatus] = useState(initialStatus || 'pending')
    const [polling, setPolling] = useState(false)
    const intervalRef = useRef(null)

    const startPolling = useCallback(() => {
        if (!documentId) return
        setPolling(true)

        const poll = async () => {
            try {
                const res = await documentsAPI.getStatus(documentId)
                const newStatus = res.data.status
                setStatus(newStatus)
                if (newStatus === 'completed' || newStatus === 'failed') {
                    stopPolling()
                    onStatusChange?.(documentId, newStatus)
                }
            } catch {
                stopPolling()
            }
        }

        poll()
        intervalRef.current = setInterval(poll, POLL_INTERVAL)
    }, [documentId, onStatusChange])

    const stopPolling = useCallback(() => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
        }
        setPolling(false)
    }, [])

    useEffect(() => {
        return () => stopPolling()
    }, [stopPolling])

    return { status, polling, startPolling, stopPolling }
}
