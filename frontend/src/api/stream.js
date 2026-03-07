import { getAccessToken } from './axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

/**
 * Streams chat response via SSE using fetch + ReadableStream.
 * Uses fetch instead of EventSource to support Authorization headers.
 *
 * @param {string} conversationId
 * @param {string} message
 * @param {object} options - { topK, similarityThreshold }
 * @param {function} onToken - called with each text token
 * @param {function} onMetadata - called with citations metadata
 * @param {function} onDone - called when stream completes
 * @param {function} onError - called on error
 * @param {AbortSignal} signal - optional abort signal
 */
export async function streamChat(
    conversationId,
    message,
    options = {},
    { onToken, onMetadata, onDone, onError, signal } = {}
) {
    const token = getAccessToken()

    try {
        const params = new URLSearchParams({
            message,
            top_k: String(options.topK || 10),
            similarity_threshold: String(options.similarityThreshold || 0.2),
        })

        const response = await fetch(
            `${API_BASE_URL}/conversations/${conversationId}/chat/stream?${params}`,
            {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                signal,
            }
        )

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || `HTTP ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
                const trimmed = line.trim()
                if (!trimmed || !trimmed.startsWith('data: ')) continue

                const payload = trimmed.slice(6)

                if (payload === '[DONE]') {
                    onDone?.()
                    return
                }

                if (payload.startsWith('[ERROR]')) {
                    onError?.(new Error(payload.slice(8)))
                    return
                }

                try {
                    const parsed = JSON.parse(payload)

                    if (typeof parsed === 'object' && parsed.type === 'metadata') {
                        onMetadata?.(parsed)
                    } else if (typeof parsed === 'string') {
                        onToken?.(parsed)
                    }
                } catch {
                    // If JSON parse fails, treat as raw text
                    onToken?.(payload)
                }
            }
        }

        onDone?.()
    } catch (error) {
        if (error.name === 'AbortError') return
        onError?.(error)
    }
}
