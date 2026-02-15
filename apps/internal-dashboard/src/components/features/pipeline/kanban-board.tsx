'use client'

import { useState } from 'react'
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

interface PipelineApplication {
  id: string
  application_id: string
  candidate_name: string
  candidate_email: string
  status: string
  current_stage_name: string | null
  is_starred: boolean
  applied_at: string
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
}: {
  application: PipelineApplication
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: application.id,
  })

  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
      }
    : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={`rounded-md border p-3 transition-all cursor-grab active:cursor-grabbing ${
        isDragging
          ? 'opacity-50 shadow-lg scale-105'
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
          <span className="ml-2 text-yellow-500" title="Starred">
            &#9733;
          </span>
        )}
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        Applied {new Date(application.applied_at).toLocaleDateString()}
      </p>
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
  return (
    <div
      className={`rounded-md border p-3 transition-all ${
        isDragging
          ? 'opacity-50 shadow-lg scale-105 rotate-2'
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
          <span className="ml-2 text-yellow-500" title="Starred">
            &#9733;
          </span>
        )}
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        Applied {new Date(application.applied_at).toLocaleDateString()}
      </p>
    </div>
  )
}

function DroppableStage({
  stage,
}: {
  stage: PipelineStage
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: `stage-${stage.id}`,
  })

  return (
    <div
      ref={setNodeRef}
      className={`h-full rounded-lg border-2 transition-colors ${
        isOver
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
              Drop candidates here
            </p>
          ) : (
            stage.applications.map((app) => (
              <div key={app.id}>
                <DraggableCard application={app} />
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

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement before drag starts
      },
    })
  )

  const handleDragStart = (event: DragStartEvent) => {
    const applicationId = event.active.id as string

    // Find the application being dragged
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

    // Find the target stage by looking at which stage contains the drop target
    let targetStageId: string | null = null
    for (const stage of stages) {
      if (stage.applications.some(a => a.id === over.id) || over.id === `stage-${stage.id}`) {
        targetStageId = stage.id
        break
      }
    }

    if (!targetStageId) return

    // Find current stage of the application
    let currentStageId: string | null = null
    for (const stage of stages) {
      if (stage.applications.find(a => a.id === applicationId)) {
        currentStageId = stage.id
        break
      }
    }

    // Don't do anything if dropped in same stage
    if (currentStageId === targetStageId) return

    // Optimistic update
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

    // Make API call
    const result = await moveApplicationToStage(applicationId, targetStageId, requisitionId)

    if (!result.success) {
      // Revert on error
      setStages(initialStages)
      alert(`Failed to move candidate: ${result.error}`)
      router.refresh()
    } else {
      // Refresh to get latest data
      router.refresh()
    }
  }

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 overflow-x-auto pb-4">
        {stages.map((stage) => (
          <div key={stage.id} className="w-72 flex-shrink-0">
            <DroppableStage stage={stage} />
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
  )
}
