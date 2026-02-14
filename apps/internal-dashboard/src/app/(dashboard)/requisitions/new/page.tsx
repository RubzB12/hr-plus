import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export const metadata = {
  title: 'New Requisition — HR-Plus',
}

export default function NewRequisitionPage() {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Create Requisition</h2>
      <Card>
        <CardHeader>
          <CardTitle>Requisition Details</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Requisition creation form will be implemented here.
            Connect the API to enable creating new requisitions.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
