'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  requisitionPublishAction,
  requisitionHoldAction,
  requisitionCancelAction,
  requisitionReopenAction,
  requisitionCloneAction,
} from './actions'

interface RequisitionActionsProps {
  requisitionId: string
  status: string
}

export function RequisitionActions({ requisitionId, status }: RequisitionActionsProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  async function handleAction(action: (id: string) => Promise<{ success: boolean; error?: string }>) {
    setLoading(true)
    try {
      const result = await action(requisitionId)
      if (!result.success) {
        alert(result.error ?? 'Action failed')
      }
    } finally {
      setLoading(false)
      router.refresh()
    }
  }

  return (
    <div className="flex gap-2">
      {status === 'approved' && (
        <Button
          size="sm"
          onClick={() => handleAction(requisitionPublishAction)}
          disabled={loading}
        >
          Publish
        </Button>
      )}
      {status === 'open' && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => handleAction(requisitionHoldAction)}
          disabled={loading}
        >
          Put on Hold
        </Button>
      )}
      {!['filled', 'cancelled'].includes(status) && (
        <Button
          size="sm"
          variant="destructive"
          onClick={() => handleAction(requisitionCancelAction)}
          disabled={loading}
        >
          Cancel
        </Button>
      )}
      {['on_hold', 'cancelled'].includes(status) && (
        <Button
          size="sm"
          onClick={() => handleAction(requisitionReopenAction)}
          disabled={loading}
        >
          Reopen
        </Button>
      )}
      <Button
        size="sm"
        variant="outline"
        onClick={() => handleAction(requisitionCloneAction)}
        disabled={loading}
      >
        Clone
      </Button>
    </div>
  )
}
