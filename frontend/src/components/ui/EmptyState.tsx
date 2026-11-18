import { CalendarDays } from 'lucide-react'

type EmptyStateProps = {
  title: string
  text: string
}

export function EmptyState({ title, text }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div>
        <CalendarDays size={21} />
      </div>
      <strong>{title}</strong>
      <p>{text}</p>
    </div>
  )
}
