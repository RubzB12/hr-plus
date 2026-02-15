'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { submitForApproval, sendToCandidate, withdrawOffer } from '@/app/(dashboard)/offers/[id]/actions'
import { Send, XCircle, CheckCircle } from 'lucide-react'

interface OfferActionsProps {
  offerId: string
  status: string
  canEdit: boolean
  canWithdraw: boolean
  canSend: boolean
}

export function OfferActions({ offerId, status, canEdit, canWithdraw, canSend }: OfferActionsProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [showApprovalDialog, setShowApprovalDialog] = useState(false)
  const [showWithdrawDialog, setShowWithdrawDialog] = useState(false)
  const [approverIds, setApproverIds] = useState<string[]>([])
  const [approverInput, setApproverInput] = useState('')

  const handleSubmitForApproval = async () => {
    if (approverIds.length === 0) {
      alert('Please add at least one approver')
      return
    }

    setLoading(true)
    try {
      const result = await submitForApproval(offerId, approverIds)
      if (result.success) {
        router.refresh()
        setShowApprovalDialog(false)
      } else {
        alert(result.error || 'Failed to submit for approval')
      }
    } catch (error) {
      alert('Failed to submit for approval')
    } finally {
      setLoading(false)
    }
  }

  const handleSendToCandidate = async () => {
    if (!confirm('Send this offer to the candidate?')) return

    setLoading(true)
    try {
      const result = await sendToCandidate(offerId)
      if (result.success) {
        router.refresh()
      } else {
        alert(result.error || 'Failed to send offer')
      }
    } catch (error) {
      alert('Failed to send offer')
    } finally {
      setLoading(false)
    }
  }

  const handleWithdraw = async () => {
    setLoading(true)
    try {
      const result = await withdrawOffer(offerId)
      if (result.success) {
        router.refresh()
        setShowWithdrawDialog(false)
      } else {
        alert(result.error || 'Failed to withdraw offer')
      }
    } catch (error) {
      alert('Failed to withdraw offer')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="flex items-center gap-2">
        {status === 'draft' && (
          <Button
            onClick={() => setShowApprovalDialog(true)}
            disabled={loading}
            className="flex items-center gap-2"
          >
            <CheckCircle className="h-4 w-4" />
            Submit for Approval
          </Button>
        )}

        {canSend && (
          <Button
            onClick={handleSendToCandidate}
            disabled={loading}
            className="flex items-center gap-2"
          >
            <Send className="h-4 w-4" />
            Send to Candidate
          </Button>
        )}

        {canWithdraw && (
          <Button
            variant="outline"
            onClick={() => setShowWithdrawDialog(true)}
            disabled={loading}
            className="flex items-center gap-2 text-destructive hover:text-destructive"
          >
            <XCircle className="h-4 w-4" />
            Withdraw Offer
          </Button>
        )}
      </div>

      {/* Submit for Approval Dialog */}
      {showApprovalDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background rounded-lg shadow-lg max-w-md w-full mx-4 p-6 space-y-4">
            <h3 className="text-lg font-semibold">Submit for Approval</h3>

            <div className="space-y-2">
              <label className="text-sm font-medium">Add Approvers (User IDs)</label>
              <div className="flex gap-2">
                <Input
                  placeholder="Enter user ID"
                  value={approverInput}
                  onChange={(e) => setApproverInput(e.target.value)}
                />
                <Button
                  type="button"
                  onClick={() => {
                    if (approverInput.trim()) {
                      setApproverIds([...approverIds, approverInput.trim()])
                      setApproverInput('')
                    }
                  }}
                >
                  Add
                </Button>
              </div>
              {approverIds.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Approvers:</p>
                  {approverIds.map((id, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-muted px-3 py-1 rounded">
                      <span className="text-sm">{id}</span>
                      <button
                        onClick={() => setApproverIds(approverIds.filter((_, i) => i !== idx))}
                        className="text-xs text-destructive hover:underline"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => setShowApprovalDialog(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSubmitForApproval}
                disabled={loading || approverIds.length === 0}
              >
                {loading ? 'Submitting...' : 'Submit'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Withdraw Dialog */}
      {showWithdrawDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background rounded-lg shadow-lg max-w-md w-full mx-4 p-6 space-y-4">
            <h3 className="text-lg font-semibold">Withdraw Offer</h3>
            <p className="text-sm text-muted-foreground">
              Are you sure you want to withdraw this offer? This action cannot be undone.
            </p>
            <div className="flex items-center gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => setShowWithdrawDialog(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleWithdraw}
                disabled={loading}
              >
                {loading ? 'Withdrawing...' : 'Withdraw Offer'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
