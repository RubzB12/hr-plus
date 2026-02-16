import { AlertCircle, AlertTriangle, Info, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ErrorMessageProps {
  message: string
  type?: 'error' | 'warning' | 'info'
  className?: string
}

export function ErrorMessage({ message, type = 'error', className }: ErrorMessageProps) {
  const icons = {
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
  }

  const colors = {
    error: 'bg-destructive/10 text-destructive border-destructive/20',
    warning: 'bg-yellow-50 text-yellow-900 border-yellow-200',
    info: 'bg-blue-50 text-blue-900 border-blue-200',
  }

  const Icon = icons[type]

  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-md border p-4',
        colors[type],
        className
      )}
      role="alert"
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium">{message}</p>
      </div>
    </div>
  )
}

interface FieldErrorProps {
  error?: string | string[]
  className?: string
}

export function FieldError({ error, className }: FieldErrorProps) {
  if (!error) return null

  const message = Array.isArray(error) ? error[0] : error

  return (
    <p className={cn('text-sm text-destructive flex items-center gap-1 mt-1', className)}>
      <AlertCircle className="h-3 w-3" />
      {message}
    </p>
  )
}
