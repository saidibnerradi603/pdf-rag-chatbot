export default function EmptyState({ icon, title, description, children }) {
    return (
        <div className="empty-state">
            {icon && <div className="empty-state-icon">{icon}</div>}
            {title && <h3>{title}</h3>}
            {description && <p>{description}</p>}
            {children && <div className="mt-md">{children}</div>}
        </div>
    )
}
