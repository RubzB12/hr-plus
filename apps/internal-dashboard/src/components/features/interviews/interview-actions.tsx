'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { cancelInterview, completeInterview } from '@/app/(dashboard)/interviews/[id]/actions'
import { XCircle, CheckCircle } from 'lucide-react'

interface InterviewActionsProps {
  interviewId: string
  status: string
}

export function InterviewActions({ interviewId, status }: InterviewActionsProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [showCancelDialog, setShowCancelDialog] = useState(false)
  const [cancellationReason, setCancellationReason] = useState('')

  const handleCancel = async () => {
    setLoading(true)
    try {
      const result = await cancelInterview(interviewId, cancellationReason)
      if (result.success) {
        router.refresh()
        setShowCancelDialog(false)
      } else {
        alert(result.error || 'Failed to cancel interview')
      }
    } catch (error) {
      alert('Failed to cancel interview')
    } finally {
      setLoading(false)
    }
  }

  const handleComplete = async () => {
    if (!confirm('Mark this interview as completed?')) return

    setLoading(true)
    try {
      const result = await completeInterview(interviewId)
      if (result.success) {
        router.refresh()
      } else {
        alert(result.error || 'Failed to mark interview complete')
      }
    } catch (error) {
      alert('Failed to mark interview complete')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="flex items-center gap-2">
        {status !== 'completed' && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleComplete}
            disabled={loading}
            className="flex items-center gap-2"
          >
            <CheckCircle className="h-4 w-4" />
            Mark Complete
          </Button>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowCancelDialog(true)}
          disabled={loading}
          className="flex items-center gap-2 text-destructive hover:text-destructive"
        >
          <XCircle className="h-4 w-4" />
          Cancel Interview
        </Button>
      </div>

      {/* Cancel Dialog */}
      {showCancelDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background rounded-lg shadow-lg max-w-md w-full mx-4 p-6 space-y-4">
            <h3 className="text-lg font-semibold">Cancel Interview</h3>
            <div className="space-y-2">
              <label className="text-sm font-medium">Reason for Cancellation</label>
              <textarea
                rows={4}
                placeholder="Please provide a reason..."
                value={cancellationReason}
                onChange={(e) => setCancellationReason(e.target.value)}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              />
            </div>
            <div className="flex items-center gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => setShowCancelDialog(false)}
                disabled={loading}
              >
                Close
              </Button>
              <Button
                variant="destructive"
                onClick={handleCancel}
                disabled={loading}
              >
                {loading ? 'Cancelling...' : 'Confirm Cancellation'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
