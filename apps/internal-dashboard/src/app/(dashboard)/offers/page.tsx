import Link from 'next/link'
import { getOffers } from '@/lib/dal'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { FileText, DollarSign, Calendar, TrendingUp, Plus, Clock } from 'lucide-react'

export const metadata = {
  title: 'Offers — HR-Plus',
}

interface Offer {
  id: string
  offer_id: string
  application_detail: {
    candidate_name: string
    requisition_title: string
  }
  version: number
  status: string
  title: string
  base_salary_display: string
  salary_currency: string
  salary_frequency: string
  start_date: string
  expiration_date: string
  created_at: string
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

const statusColors: Record<string, string> = {
  draft: 'text-gray-600',
  pending_approval: 'text-yellow-600',
  approved: 'text-blue-600',
  sent: 'text-indigo-600',
  viewed: 'text-purple-600',
  accepted: 'text-green-700',
  declined: 'text-red-700',
  expired: 'text-red-600',
  withdrawn: 'text-gray-500',
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
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default async function OffersPage() {
  const data = await getOffers()
  const offers: Offer[] = data.results || []

  // Separate offers by status
  const activeOffers = offers.filter(o =>
    ['sent', 'viewed', 'approved', 'pending_approval'].includes(o.status)
  )
  const acceptedOffers = offers.filter(o => o.status === 'accepted')
  const draftOffers = offers.filter(o => o.status === 'draft')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Offers</h1>
          <p className="text-muted-foreground mt-2">
            Create and manage job offers for candidates
          </p>
        </div>
        <Button asChild>
          <Link href="/offers/create" className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Create Offer
          </Link>
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Offers</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeOffers.length}</div>
            <p className="text-xs text-muted-foreground">
              Pending or sent to candidates
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Accepted</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{acceptedOffers.length}</div>
            <p className="text-xs text-muted-foreground">
              This month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Drafts</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{draftOffers.length}</div>
            <p className="text-xs text-muted-foreground">
              Awaiting submission
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(
                acceptedOffers
                  .reduce((sum, offer) => sum + parseFloat(offer.base_salary_display || '0'), 0)
                  .toString(),
                'ZAR'
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Accepted offers (annual)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Offers List */}
      <div>
        <h2 className="text-xl font-semibold mb-4">All Offers</h2>
        {offers.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No offers yet</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Create your first offer to get started
              </p>
              <Button asChild>
                <Link href="/offers/create">
                  <Plus className="h-4 w-4 mr-2" />
                  Create Offer
                </Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {offers.map((offer) => (
              <Card key={offer.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-lg">{offer.application_detail.candidate_name}</h3>
                        <Badge variant={statusVariant[offer.status] || 'outline'} className="text-xs">
                          {offer.status.replace('_', ' ').toUpperCase()}
                        </Badge>
                        {offer.version > 1 && (
                          <Badge variant="outline" className="text-xs">
                            v{offer.version}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        {offer.title} • {offer.application_detail.requisition_title}
                      </p>

                      <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-4 mb-4">
                        <div className="flex items-center gap-2 text-sm">
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">
                            {formatCurrency(offer.base_salary_display, offer.salary_currency)}
                          </span>
                          <span className="text-muted-foreground">
                            /{offer.salary_frequency === 'annual' ? 'year' : 'hour'}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 text-sm">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span>Start: {formatDate(offer.start_date)}</span>
                        </div>

                        <div className="flex items-center gap-2 text-sm">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span>Expires: {formatDate(offer.expiration_date)}</span>
                        </div>

                        <div className="flex items-center gap-2 text-sm">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <span className="text-muted-foreground">{offer.offer_id}</span>
                        </div>
                      </div>
                    </div>

                    <Button size="sm" asChild>
                      <Link href={`/offers/${offer.id}`}>
                        View Details
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
