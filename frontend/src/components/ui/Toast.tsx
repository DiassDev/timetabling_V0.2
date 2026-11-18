import { Check } from 'lucide-react'

type ToastProps = {
  message: string
}

export function Toast({ message }: ToastProps) {
  if (!message) return null

  return (
    <div className="toast">
      <Check size={16} />
      {message}
    </div>
  )
}
