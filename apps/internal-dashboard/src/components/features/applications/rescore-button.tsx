'use client'

import { useState, useTransition } from 'react'
import { RefreshCw } from 'lucide-react'
import { toast } from 'sonner'

interface RescoreButtonProps {
  applicationId: string
  action: (id: string) => Promise<{ success: boolean; error?: string }>
}

export function RescoreButton({ applicationId, action }: RescoreButtonProps) {
  const [isPending, startTransition] = useTransition()
  const [done, setDone] = useState(false)

  function handleClick() {
    startTransition(async () => {
      const result = await action(applicationId)
      if (result.success) {
        toast.success('Application scored successfully')
        setDone(true)
      } else {
        toast.error(result.error ?? 'Scoring failed')
      }
    })
  }

  if (done) return null

  return (
    <button
      onClick={handleClick}
      disabled={isPending}
      className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors disabled:opacity-50"
    >
      <RefreshCw className={`h-3.5 w-3.5 ${isPending ? 'animate-spin' : ''}`} />
      {isPending ? 'Scoring…' : 'Compute Score'}
    </button>
  )
}
