'use client'

import { useState, useTransition } from 'react'
import { toast } from 'sonner'
import { Star, ArrowRightLeft, MessageSquarePlus, XCircle, Calendar } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import {
  toggleStar,
  moveToStage,
  rejectApplication,
  addNote,
} from '@/app/(dashboard)/applications/[id]/actions'

interface Stage {
  id: string
  name: string
  order: number
  stage_type: string
}

interface ApplicationActionsPanelProps {
  applicationId: string
  isStarred: boolean
  currentStageName: string | null
  stages: Stage[]
  status: string
  candidateName: string
}

export function ApplicationActionsPanel({
  applicationId,
  isStarred,
  currentStageName,
  stages,
  status,
  candidateName,
}: ApplicationActionsPanelProps) {
  const [isPending, startTransition] = useTransition()
  const [noteOpen, setNoteOpen] = useState(false)
  const [rejectOpen, setRejectOpen] = useState(false)
  const [noteText, setNoteText] = useState('')
  const [notePrivate, setNotePrivate] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  const isTerminal = ['hired', 'rejected', 'withdrawn'].includes(status)
  const availableStages = stages.filter((s) => s.name !== currentStageName)

  function handleStar() {
    startTransition(async () => {
      const result = await toggleStar(applicationId)
      if (result.success) {
        toast.success(isStarred ? 'Removed from starred' : 'Application starred')
      } else {
        toast.error(result.error ?? 'Failed to update star')
      }
    })
  }

  function handleMoveToStage(stageId: string, stageName: string) {
    startTransition(async () => {
      const result = await moveToStage(applicationId, stageId)
      if (result.success) {
        toast.success(`Moved to ${stageName}`)
      } else {
        toast.error(result.error ?? 'Failed to move stage')
      }
    })
  }

  function handleAddNote() {
    if (!noteText.trim()) return
    startTransition(async () => {
      const result = await addNote(applicationId, noteText.trim(), notePrivate)
      if (result.success) {
        toast.success('Note added')
        setNoteText('')
        setNotePrivate(false)
        setNoteOpen(false)
      } else {
        toast.error(result.error ?? 'Failed to add note')
      }
    })
  }

  function handleReject() {
    if (!rejectReason.trim()) return
    startTransition(async () => {
      const result = await rejectApplication(applicationId, rejectReason.trim())
      if (result.success) {
        toast.success('Application rejected')
        setRejectReason('')
        setRejectOpen(false)
      } else {
        toast.error(result.error ?? 'Failed to reject application')
      }
    })
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Star / Unstar */}
      <Button
        variant="outline"
        size="sm"
        onClick={handleStar}
        disabled={isPending}
        className={isStarred ? 'border-yellow-400 text-yellow-600 hover:bg-yellow-50' : ''}
      >
        <Star className={`h-4 w-4 ${isStarred ? 'fill-yellow-400 text-yellow-500' : ''}`} />
        {isStarred ? 'Starred' : 'Star'}
      </Button>

      {/* Move to Stage */}
      {!isTerminal && availableStages.length > 0 && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" disabled={isPending}>
              <ArrowRightLeft className="h-4 w-4" />
              Move Stage
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            {availableStages.map((stage) => (
              <DropdownMenuItem
                key={stage.id}
                onClick={() => handleMoveToStage(stage.id, stage.name)}
              >
                {stage.name}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      )}

      {/* Add Note */}
      <Dialog open={noteOpen} onOpenChange={setNoteOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm">
            <MessageSquarePlus className="h-4 w-4" />
            Add Note
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Note</DialogTitle>
            <DialogDescription>
              Add a note to {candidateName}&apos;s application.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="note-body">Note</Label>
              <textarea
                id="note-body"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm min-h-[120px] resize-y focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Write your note here..."
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="note-private"
                checked={notePrivate}
                onChange={(e) => setNotePrivate(e.target.checked)}
                className="h-4 w-4 rounded border"
              />
              <Label htmlFor="note-private" className="font-normal text-sm cursor-pointer">
                Private (only visible to you)
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setNoteOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddNote} disabled={!noteText.trim() || isPending}>
              Add Note
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Schedule Interview */}
      {!isTerminal && (
        <Button variant="outline" size="sm" asChild>
          <Link href={`/interviews/schedule?applicationId=${applicationId}`}>
            <Calendar className="h-4 w-4" />
            Schedule Interview
          </Link>
        </Button>
      )}

      {/* Reject */}
      {!isTerminal && (
        <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
          <DialogTrigger asChild>
            <Button variant="destructive" size="sm">
              <XCircle className="h-4 w-4" />
              Reject
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Reject Application</DialogTitle>
              <DialogDescription>
                Provide a reason for rejecting {candidateName}&apos;s application. This will be
                recorded in the audit trail.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-1.5">
              <Label htmlFor="reject-reason">Reason</Label>
              <Input
                id="reject-reason"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="e.g. Not enough experience, position filled..."
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setRejectOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleReject}
                disabled={!rejectReason.trim() || isPending}
              >
                Confirm Rejection
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}
