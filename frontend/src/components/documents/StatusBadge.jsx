export default function StatusBadge({ status }) {
    const labels = {
        pending: 'Pending',
        processing: 'Processing',
        completed: 'Ready',
        failed: 'Failed',
    }

    return (
        <span className={`status-badge ${status}`}>
            <span className={`status-dot ${status}`} />
            {labels[status] || status}
        </span>
    )
}
