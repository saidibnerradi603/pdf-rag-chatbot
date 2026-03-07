import { useState, useCallback, useEffect } from 'react'
import { documentsAPI } from '../api/documents'
import { getErrorMessage } from '../utils/helpers'
import toast from 'react-hot-toast'

export function useDocuments(initialFilter = 'completed') {
    const [documents, setDocuments] = useState([])
    const [loading, setLoading] = useState(true)
    const [statusFilter, setStatusFilter] = useState(initialFilter)

    const fetchDocuments = useCallback(async (filter) => {
        const activeFilter = filter || statusFilter
        setLoading(true)
        try {
            const res = await documentsAPI.list(activeFilter)
            setDocuments(res.data)
        } catch (err) {
            toast.error(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }, [statusFilter])

    useEffect(() => {
        fetchDocuments(statusFilter)
    }, [statusFilter])

    const changeFilter = useCallback((newFilter) => {
        setStatusFilter(newFilter)
    }, [])

    const uploadDocument = useCallback(async (file, onProgress) => {
        const res = await documentsAPI.upload(file, (progressEvent) => {
            const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress?.(pct)
        })
        return res.data
    }, [])

    const processDocument = useCallback(async (documentId) => {
        const res = await documentsAPI.process(documentId)
        return res.data
    }, [])

    const deleteDocument = useCallback(async (documentId) => {
        await documentsAPI.delete(documentId)
        setDocuments((prev) => prev.filter((d) => d.id !== documentId))
        toast.success('Document deleted')
    }, [])

    const getDownloadUrl = useCallback(async (documentId) => {
        const res = await documentsAPI.getDownloadUrl(documentId)
        return res.data.download_url
    }, [])

    return {
        documents,
        loading,
        statusFilter,
        changeFilter,
        fetchDocuments,
        uploadDocument,
        processDocument,
        deleteDocument,
        getDownloadUrl,
    }
}
