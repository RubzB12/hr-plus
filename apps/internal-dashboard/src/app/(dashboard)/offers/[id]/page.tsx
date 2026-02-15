import { notFound } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, DollarSign, Calendar, User, FileText, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getOfferDetail } from '@/lib/dal'
import { OfferActions } from '@/components/features/offers/offer-actions'
import { ApprovalWorkflow } from '@/components/features/offers/approval-workflow'

export const metadata = {
  title: 'Offer Details — HR-Plus',
}

interface OfferDetailPageProps {
  params: Promise<{ id: string }>
}

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  draft: 'outline',
  pending_approval: 'secondary',
  approved: 'default',
  sent: 'default',
  viewed: 'secondary',
  accepted: 'default',
  declined: 'destructive',
  expired: 'destructive',
  withdrawn: 'destructive',
}

function formatCurrency(amount: string, currency: string) {
  const num = parseFloat(amount)
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num)
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

export default async function OfferDetailPage({ params }: OfferDetailPageProps) {
  const { id } = await params

  let offer: any

  try {
    offer = await getOfferDetail(id)
  } catch (error) {
    notFound()
  }

  const canEdit = offer.status === 'draft'
  const canApprove = offer.status === 'pending_approval'
  const canSend = offer.status === 'approved'
  const canWithdraw = ['draft', 'pending_approval', 'approved', 'sent', 'viewed'].includes(offer.status)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/offers" className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Offers
          </Link>
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">Offer {offer.offer_id}</h1>
            <Badge variant={statusVariant[offer.status] ?? 'secondary'}>
              {offer.status.replace('_', ' ').toUpperCase()}
            </Badge>
            {offer.version > 1 && (
              <Badge variant="outline">
                Version {offer.version}
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground mt-2">
            {offer.application_detail.candidate_name} • {offer.application_detail.requisition_title}
          </p>
        </div>
        <OfferActions
          offerId={id}
          status={offer.status}
          canEdit={canEdit}
          canWithdraw={canWithdraw}
          canSend={canSend}
        />
      </div>

      {/* Approval Workflow */}
      {(offer.status === 'pending_approval' || offer.status === 'approved') && offer.approvals && (
        <ApprovalWorkflow approvals={offer.approvals} offerId={id} />
      )}

      {/* Offer Details */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Candidate & Position
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Candidate</p>
              <p className="text-sm">{offer.application_detail.candidate_name}</p>
              <p className="text-xs text-muted-foreground">{offer.application_detail.candidate_email}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground">Job Title</p>
              <p className="text-sm font-semibold">{offer.title}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground">Level</p>
              <p className="text-sm">{offer.level_detail?.name || 'N/A'}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground">Department</p>
              <p className="text-sm">{offer.department_name || 'N/A'}</p>
            </div>

            {offer.reporting_to_name && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">Reports To</p>
                <p className="text-sm">{offer.reporting_to_name}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5" />
              Compensation Package
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Base Salary</p>
              <p className="text-2xl font-bold">
                {formatCurrency(offer.base_salary_display, offer.salary_currency)}
              </p>
              <p className="text-xs text-muted-foreground">
                per {offer.salary_frequency === 'annual' ? 'year' : 'hour'}
              </p>
            </div>

            {offer.bonus_display && parseFloat(offer.bonus_display) > 0 && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">Performance Bonus</p>
                <p className="text-sm font-semibold">
                  {formatCurrency(offer.bonus_display, offer.salary_currency)}
                </p>
              </div>
            )}

            {offer.sign_on_bonus_display && parseFloat(offer.sign_on_bonus_display) > 0 && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">Sign-on Bonus</p>
                <p className="text-sm font-semibold">
                  {formatCurrency(offer.sign_on_bonus_display, offer.salary_currency)}
                </p>
              </div>
            )}

            {offer.relocation_display && parseFloat(offer.relocation_display) > 0 && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">Relocation Package</p>
                <p className="text-sm font-semibold">
                  {formatCurrency(offer.relocation_display, offer.salary_currency)}
                </p>
              </div>
            )}

            {offer.equity && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">Equity</p>
                <p className="text-sm">{offer.equity}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Dates & Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Important Dates
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">Start Date</p>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">{formatDate(offer.start_date)}</span>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">Expiration Date</p>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">{formatDate(offer.expiration_date)}</span>
              </div>
            </div>

            {offer.sent_at && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-1">Sent to Candidate</p>
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="text-sm">{formatDate(offer.sent_at)}</span>
                </div>
              </div>
            )}

            {offer.viewed_at && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-1">Viewed by Candidate</p>
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-blue-600" />
                  <span className="text-sm">{formatDate(offer.viewed_at)}</span>
                </div>
              </div>
            )}

            {offer.responded_at && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-1">Response Date</p>
                <div className="flex items-center gap-2">
                  {offer.status === 'accepted' ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-600" />
                  )}
                  <span className="text-sm">{formatDate(offer.responded_at)}</span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Internal Notes */}
      {offer.notes && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Internal Notes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md">
              {offer.notes}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Decline Reason */}
      {offer.status === 'declined' && offer.decline_reason && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Decline Reason
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap">
              {offer.decline_reason}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Offer Information</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 md:grid-cols-2 text-xs text-muted-foreground">
          <div>
            <span className="font-medium">Created by:</span> {offer.created_by_detail?.user_name || 'Unknown'}
          </div>
          <div>
            <span className="font-medium">Created on:</span> {formatDate(offer.created_at)}
          </div>
          <div>
            <span className="font-medium">Last updated:</span> {formatDate(offer.updated_at)}
          </div>
          <div>
            <span className="font-medium">Application ID:</span> {offer.application_detail.application_id}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
