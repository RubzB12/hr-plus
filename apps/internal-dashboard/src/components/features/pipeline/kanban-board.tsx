'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
  useDraggable,
} from '@dnd-kit/core'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { moveApplicationToStage } from '@/app/(dashboard)/requisitions/[id]/pipeline/actions'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { GitCompare, X, CheckSquare } from 'lucide-react'
import { ScoreBadge } from '@/components/features/applications/score-badge'

interface PipelineApplication {
  id: string
  application_id: string
  candidate_name: string
  candidate_email: string
  status: string
  current_stage_name: string | null
  is_starred: boolean
  applied_at: string
  stage_entered_at?: string
  final_score?: number | null
}

function getDaysInStage(dateStr?: string): number {
  const date = dateStr ? new Date(dateStr) : new Date()
  const now = new Date()
  return Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
}

function getStageDurationClass(days: number): string {
  if (days > 7) return 'text-red-600 font-semibold'
  if (days > 3) return 'text-yellow-600'
  return 'text-muted-foreground'
}

interface PipelineStage {
  id: string
  name: string
  order: number
  stage_type: string
  application_count: number
  applications: PipelineApplication[]
}

interface KanbanBoardProps {
  stages: PipelineStage[]
  requisitionId: string
}

const stageTypeVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  sourced: 'outline',
  applied: 'outline',
  screening: 'secondary',
  interview: 'default',
  offer: 'default',
  hired: 'default',
  rejected: 'destructive',
}

function DraggableCard({
  application,
  isSelecting,
  isSelected,
  onToggleSelect,
}: {
  application: PipelineApplication
  isSelecting: boolean
  isSelected: boolean
  onToggleSelect: (id: string) => void
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: application.id,
    disabled: isSelecting,
  })

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
      }
    : undefined

  const days = getDaysInStage(application.stage_entered_at ?? application.applied_at)
  const durationClass = getStageDurationClass(days)

  if (isSelecting) {
    return (
      <button
        onClick={() => onToggleSelect(application.id)}
        className={`w-full text-left rounded-md border transition-all p-3 ${
          isSelected
            ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
            : 'hover:shadow-md hover:border-primary/40'
        }`}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{application.candidate_name}</p>
            <p className="truncate text-xs text-muted-foreground">{application.candidate_email}</p>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {application.is_starred && (
              <span className="text-yellow-500" title="Starred">&#9733;</span>
            )}
            <div
              className={`h-4 w-4 rounded border-2 flex items-center justify-center ${
                isSelected ? 'border-primary bg-primary' : 'border-muted-foreground'
              }`}
            >
              {isSelected && <span className="text-white text-[10px] font-bold">✓</span>}
            </div>
          </div>
        </div>
        <div className="mt-2 flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Applied {new Date(application.applied_at).toLocaleDateString()}
          </p>
          <span className={`text-xs ${durationClass}`} title={`${days} days in this stage`}>
            {days}d in stage
          </span>
        </div>
      </button>
    )
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`rounded-md border transition-all ${
        isDragging
          ? 'opacity-50 shadow-lg scale-105'
          : 'hover:shadow-md'
      }`}
    >
      {/* Drag handle area */}
      <div
        {...listeners}
        {...attributes}
        className="p-3 cursor-grab active:cursor-grabbing"
      >
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <Link
              href={`/applications/${application.id}`}
              className="truncate text-sm font-medium hover:underline block"
              onClick={(e) => e.stopPropagation()}
            >
              {application.candidate_name}
            </Link>
            <p className="truncate text-xs text-muted-foreground">
              {application.candidate_email}
            </p>
          </div>
          {application.is_starred && (
            <span className="ml-2 text-yellow-500 shrink-0" title="Starred">
              &#9733;
            </span>
          )}
        </div>
        <div className="mt-2 flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Applied {new Date(application.applied_at).toLocaleDateString()}
          </p>
          <div className="flex items-center gap-1.5">
            <ScoreBadge score={application.final_score} size="sm" />
            <span className={`text-xs ${durationClass}`} title={`${days} days in this stage`}>
              {days}d
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

function CandidateCard({
  application,
  isDragging = false,
}: {
  application: PipelineApplication
  isDragging?: boolean
}) {
  const days = getDaysInStage(application.stage_entered_at ?? application.applied_at)
  const durationClass = getStageDurationClass(days)

  return (
    <div
      className={`rounded-md border p-3 bg-background transition-all ${
        isDragging
          ? 'shadow-lg scale-105 rotate-2'
          : 'hover:bg-muted/50 hover:shadow-md'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">
            {application.candidate_name}
          </p>
          <p className="truncate text-xs text-muted-foreground">
            {application.candidate_email}
          </p>
        </div>
        {application.is_starred && (
          <span className="ml-2 text-yellow-500 shrink-0" title="Starred">
            &#9733;
          </span>
        )}
      </div>
      <div className="mt-2 flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          Applied {new Date(application.applied_at).toLocaleDateString()}
        </p>
        <div className="flex items-center gap-1.5">
          <ScoreBadge score={application.final_score} size="sm" />
          <span className={`text-xs ${durationClass}`}>
            {days}d
          </span>
        </div>
      </div>
    </div>
  )
}

function DroppableStage({
  stage,
  isSelecting,
  selectedIds,
  onToggleSelect,
}: {
  stage: PipelineStage
  isSelecting: boolean
  selectedIds: Set<string>
  onToggleSelect: (id: string) => void
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: `stage-${stage.id}`,
  })

  return (
    <div
      ref={setNodeRef}
      className={`h-full rounded-lg border-2 transition-colors ${
        isOver && !isSelecting
          ? 'border-primary bg-primary/5'
          : 'border-transparent'
      }`}
    >
      <Card className="h-full">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">
              {stage.name}
            </CardTitle>
            <Badge variant={stageTypeVariant[stage.stage_type] ?? 'secondary'}>
              {stage.application_count}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 min-h-[200px]">
          {stage.applications.length === 0 ? (
            <p className="py-8 text-center text-xs text-muted-foreground">
              {isSelecting ? 'No candidates' : 'Drop candidates here'}
            </p>
          ) : (
            stage.applications.map((app) => (
              <div key={app.id}>
                <DraggableCard
                  application={app}
                  isSelecting={isSelecting}
                  isSelected={selectedIds.has(app.id)}
                  onToggleSelect={onToggleSelect}
                />
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export function KanbanBoard({ stages: initialStages, requisitionId }: KanbanBoardProps) {
  const router = useRouter()
  const [stages, setStages] = useState(initialStages)
  const [activeApplication, setActiveApplication] = useState<PipelineApplication | null>(null)
  const [isSelecting, setIsSelecting] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement before drag starts
      },
    })
  )

  const handleDragStart = (event: DragStartEvent) => {
    if (isSelecting) return
    const applicationId = event.active.id as string
    for (const stage of stages) {
      const app = stage.applications.find(a => a.id === applicationId)
      if (app) {
        setActiveApplication(app)
        break
      }
    }
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event

    setActiveApplication(null)

    if (!over) return

    const applicationId = active.id as string

    let targetStageId: string | null = null
    for (const stage of stages) {
      if (stage.applications.some(a => a.id === over.id) || over.id === `stage-${stage.id}`) {
        targetStageId = stage.id
        break
      }
    }

    if (!targetStageId) return

    let currentStageId: string | null = null
    for (const stage of stages) {
      if (stage.applications.find(a => a.id === applicationId)) {
        currentStageId = stage.id
        break
      }
    }

    if (currentStageId === targetStageId) return

    const newStages = stages.map(stage => {
      if (stage.id === currentStageId) {
        return {
          ...stage,
          applications: stage.applications.filter(a => a.id !== applicationId),
          application_count: stage.application_count - 1,
        }
      }
      if (stage.id === targetStageId) {
        const movedApp = stages
          .find(s => s.id === currentStageId)
          ?.applications.find(a => a.id === applicationId)

        if (movedApp) {
          return {
            ...stage,
            applications: [...stage.applications, movedApp],
            application_count: stage.application_count + 1,
          }
        }
      }
      return stage
    })

    setStages(newStages)

    const result = await moveApplicationToStage(applicationId, targetStageId, requisitionId)

    if (!result.success) {
      setStages(initialStages)
      toast.error(result.error ?? 'Failed to move candidate')
      router.refresh()
    } else {
      toast.success('Candidate moved')
      router.refresh()
    }
  }

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else if (next.size < 4) {
        next.add(id)
      }
      return next
    })
  }

  function enterSelectMode() {
    setIsSelecting(true)
    setSelectedIds(new Set())
  }

  function exitSelectMode() {
    setIsSelecting(false)
    setSelectedIds(new Set())
  }

  const compareUrl = `/compare?ids=${Array.from(selectedIds).join(',')}&from=${encodeURIComponent(`/requisitions/${requisitionId}/pipeline`)}`

  return (
    <div className="relative">
      {/* Board controls */}
      <div className="mb-3 flex items-center justify-end gap-2">
        {!isSelecting ? (
          <button
            onClick={enterSelectMode}
            className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <CheckSquare className="h-3.5 w-3.5" />
            Select to Compare
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {selectedIds.size}/4 selected
            </span>
            <button
              onClick={exitSelectMode}
              className="flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs text-muted-foreground hover:bg-muted transition-colors"
            >
              <X className="h-3 w-3" />
              Cancel
            </button>
          </div>
        )}
      </div>

      <DndContext
        sensors={sensors}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4">
          {stages.map((stage) => (
            <div key={stage.id} className="w-72 flex-shrink-0">
              <DroppableStage
                stage={stage}
                isSelecting={isSelecting}
                selectedIds={selectedIds}
                onToggleSelect={toggleSelect}
              />
            </div>
          ))}
        </div>

        <DragOverlay>
          {activeApplication ? (
            <div className="w-64">
              <CandidateCard application={activeApplication} isDragging />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Floating compare bar */}
      {isSelecting && selectedIds.size >= 2 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 rounded-full border bg-background px-5 py-3 shadow-lg">
          <span className="text-sm font-medium">
            {selectedIds.size} candidate{selectedIds.size !== 1 ? 's' : ''} selected
          </span>
          <Link
            href={compareUrl}
            className="flex items-center gap-1.5 rounded-full bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <GitCompare className="h-3.5 w-3.5" />
            Compare
          </Link>
          <button
            onClick={() => setSelectedIds(new Set())}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  )
}
