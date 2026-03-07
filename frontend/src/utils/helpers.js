import { format, isToday, isYesterday } from 'date-fns'

export function formatDate(dateStr) {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    if (isToday(date)) return format(date, 'h:mm a')
    if (isYesterday(date)) return 'Yesterday'
    return format(date, 'MMM d, yyyy')
}

export function formatTime(dateStr) {
    if (!dateStr) return ''
    return format(new Date(dateStr), 'h:mm a')
}

export function formatFileSize(sizeStr) {
    if (!sizeStr) return ''
    return sizeStr
}

export function getInitials(email) {
    if (!email) return '?'
    return email.charAt(0).toUpperCase()
}

export function truncate(text, maxLen = 40) {
    if (!text || text.length <= maxLen) return text
    return text.slice(0, maxLen) + '...'
}

export function getErrorMessage(error) {
    if (error?.response?.data?.detail) {
        const detail = error.response.data.detail
        if (typeof detail === 'string') return detail
        if (Array.isArray(detail)) {
            return detail.map((d) => d.msg || d.message || String(d)).join(', ')
        }
        return JSON.stringify(detail)
    }
    if (error?.message) return error.message
    return 'An unexpected error occurred'
}
