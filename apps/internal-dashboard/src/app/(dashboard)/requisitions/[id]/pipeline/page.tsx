import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getPipelineBoard, getRequisitionDetail } from '@/lib/dal'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { KanbanBoard } from '@/components/features/pipeline/kanban-board'

export const metadata = {
  title: 'Pipeline Board — HR-Plus',
}

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

interface RequisitionDetail {
  id: string
  requisition_id: string
  title: string
  status: string
}

export default async function PipelineBoardPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  let requisition: RequisitionDetail
  let stages: PipelineStage[]

  try {
    ;[requisition, stages] = await Promise.all([
      getRequisitionDetail(id),
      getPipelineBoard(id),
    ])
  } catch {
    notFound()
  }

  const totalApplications = stages.reduce(
    (sum, stage) => sum + stage.application_count,
    0
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link href={`/requisitions/${id}`}>Back</Link>
            </Button>
            <h2 className="text-lg font-semibold">{requisition.title}</h2>
            <Badge variant="outline">{requisition.requisition_id}</Badge>
          </div>
          <p className="ml-14 text-sm text-muted-foreground">
            Pipeline Board &middot; {totalApplications} application{totalApplications !== 1 ? 's' : ''}
            &middot; <span className="text-primary">Drag & drop to move candidates</span>
          </p>
        </div>
      </div>

      {stages.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No pipeline stages configured for this requisition.
          </CardContent>
        </Card>
      ) : (
        <KanbanBoard stages={stages} requisitionId={id} />
      )}
    </div>
  )
}
