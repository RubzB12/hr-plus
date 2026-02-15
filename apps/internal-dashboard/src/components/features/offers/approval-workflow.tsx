'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CheckCircle, XCircle, Clock, User } from 'lucide-react'
import { approveOffer, rejectOffer } from '@/app/(dashboard)/offers/[id]/actions'

interface Approval {
  id: string
  approver_detail: {
    user_name: string
    title: string
  }
  order: number
  status: string
  comments: string
  decided_at: string | null
}

interface ApprovalWorkflowProps {
  approvals: Approval[]
  offerId: string
}

export function ApprovalWorkflow({ approvals, offerId }: ApprovalWorkflowProps) {
  const router = useRouter()
  const [loading, setLoading] = useState<string | null>(null)
  const [showCommentDialog, setShowCommentDialog] = useState<{ id: string; action: 'approve' | 'reject' } | null>(null)
  const [comments, setComments] = useState('')

  const sortedApprovals = [...approvals].sort((a, b) => a.order - b.order)

  const handleApprove = async (approvalId: string) => {
    setLoading(approvalId)
    try {
      const result = await approveOffer(approvalId, comments)
      if (result.success) {
        router.refresh()
        setShowCommentDialog(null)
        setComments('')
      } else {
        alert(result.error || 'Failed to approve')
      }
    } catch (error) {
      alert('Failed to approve')
    } finally {
      setLoading(null)
    }
  }

  const handleReject = async (approvalId: string) => {
    if (!comments.trim()) {
      alert('Comments required for rejection')
      return
    }

    setLoading(approvalId)
    try {
      const result = await rejectOffer(approvalId, comments)
      if (result.success) {
        router.refresh()
        setShowCommentDialog(null)
        setComments('')
      } else {
        alert(result.error || 'Failed to reject')
      }
    } catch (error) {
      alert('Failed to reject')
    } finally {
      setLoading(null)
    }
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Approval Workflow
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sortedApprovals.map((approval, idx) => (
              <div key={approval.id} className="flex items-start gap-4 pb-4 border-b last:border-0">
                <div className="flex-shrink-0">
                  {approval.status === 'approved' ? (
                    <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                      <CheckCircle className="h-6 w-6 text-green-700" />
                    </div>
                  ) : approval.status === 'rejected' ? (
                    <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
                      <XCircle className="h-6 w-6 text-red-700" />
                    </div>
                  ) : (
                    <div className="h-10 w-10 rounded-full bg-yellow-100 flex items-center justify-center">
                      <Clock className="h-6 w-6 text-yellow-700" />
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-medium">{approval.approver_detail.user_name}</p>
                    <Badge variant="outline" className="text-xs">
                      Step {idx + 1}
                    </Badge>
                    <Badge
                      variant={
                        approval.status === 'approved'
                          ? 'default'
                          : approval.status === 'rejected'
                          ? 'destructive'
                          : 'secondary'
                      }
                      className="text-xs"
                    >
                      {approval.status.toUpperCase()}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{approval.approver_detail.title}</p>

                  {approval.comments && (
                    <div className="mt-2 p-2 bg-muted rounded text-sm">
                      <p className="font-medium text-xs text-muted-foreground mb-1">Comments:</p>
                      <p className="whitespace-pre-wrap">{approval.comments}</p>
                    </div>
                  )}

                  {approval.decided_at && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Decided on {new Date(approval.decided_at).toLocaleDateString()}
                    </p>
                  )}

                  {approval.status === 'pending' && (
                    <div className="flex items-center gap-2 mt-3">
                      <Button
                        size="sm"
                        onClick={() => setShowCommentDialog({ id: approval.id, action: 'approve' })}
                        disabled={loading !== null}
                        className="flex items-center gap-1"
                      >
                        <CheckCircle className="h-4 w-4" />
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setShowCommentDialog({ id: approval.id, action: 'reject' })}
                        disabled={loading !== null}
                        className="flex items-center gap-1 text-destructive hover:text-destructive"
                      >
                        <XCircle className="h-4 w-4" />
                        Reject
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Comment Dialog */}
      {showCommentDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background rounded-lg shadow-lg max-w-md w-full mx-4 p-6 space-y-4">
            <h3 className="text-lg font-semibold">
              {showCommentDialog.action === 'approve' ? 'Approve Offer' : 'Reject Offer'}
            </h3>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Comments {showCommentDialog.action === 'reject' && <span className="text-destructive">*</span>}
              </label>
              <textarea
                rows={4}
                placeholder={
                  showCommentDialog.action === 'approve'
                    ? 'Optional comments...'
                    : 'Please provide a reason for rejection...'
                }
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              />
            </div>

            <div className="flex items-center gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => {
                  setShowCommentDialog(null)
                  setComments('')
                }}
                disabled={loading !== null}
              >
                Cancel
              </Button>
              <Button
                variant={showCommentDialog.action === 'approve' ? 'default' : 'destructive'}
                onClick={() =>
                  showCommentDialog.action === 'approve'
                    ? handleApprove(showCommentDialog.id)
                    : handleReject(showCommentDialog.id)
                }
                disabled={loading !== null || (showCommentDialog.action === 'reject' && !comments.trim())}
              >
                {loading !== null
                  ? 'Processing...'
                  : showCommentDialog.action === 'approve'
                  ? 'Approve'
                  : 'Reject'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
