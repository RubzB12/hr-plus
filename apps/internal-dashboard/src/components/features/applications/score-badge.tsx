import { cn } from '@/lib/utils'

interface ScoreBadgeProps {
  score: number | null | undefined
  size?: 'sm' | 'md'
}

function getScoreConfig(score: number | null | undefined): {
  label: string
  className: string
} {
  if (score == null) {
    return { label: '—', className: 'bg-muted text-muted-foreground' }
  }
  if (score >= 80) {
    return { label: String(score), className: 'bg-green-100 text-green-700 font-semibold' }
  }
  if (score >= 60) {
    return { label: String(score), className: 'bg-blue-100 text-blue-700 font-semibold' }
  }
  if (score >= 40) {
    return { label: String(score), className: 'bg-yellow-100 text-yellow-700 font-semibold' }
  }
  return { label: String(score), className: 'bg-red-100 text-red-700 font-semibold' }
}

export function ScoreBadge({ score, size = 'md' }: ScoreBadgeProps) {
  const { label, className } = getScoreConfig(score)

  return (
    <span
      title={score != null ? `Score: ${score}/100` : 'Not yet scored'}
      className={cn(
        'inline-flex items-center justify-center rounded-full tabular-nums',
        className,
        size === 'sm' ? 'h-5 min-w-[1.75rem] px-1 text-[10px]' : 'h-6 min-w-[2.25rem] px-1.5 text-xs',
      )}
    >
      {label}
    </span>
  )
}
