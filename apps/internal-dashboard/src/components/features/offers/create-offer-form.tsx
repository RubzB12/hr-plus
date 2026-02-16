'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { createOffer } from '@/app/(dashboard)/offers/create/actions'

interface CreateOfferFormProps {
  applications: any[]
  departments: any[]
  jobLevels: any[]
  managers: any[]
}

export function CreateOfferForm({
  applications,
  departments,
  jobLevels,
  managers,
}: CreateOfferFormProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedApplication, setSelectedApplication] = useState('')

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const formData = new FormData(e.currentTarget)
      const result = await createOffer(formData)

      if (result.success) {
        router.push(`/offers/${result.offerId}`)
      } else {
        setError(result.error || 'Failed to create offer')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create offer')
    } finally {
      setLoading(false)
    }
  }

  // Auto-fill details when application is selected
  const selectedApp = applications.find(app => app.id === selectedApplication)

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Candidate Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Candidate Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Select Application *</label>
            <select
              name="application"
              required
              value={selectedApplication}
              onChange={(e) => setSelectedApplication(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            >
              <option value="">-- Select an application --</option>
              {applications.map((app) => (
                <option key={app.id} value={app.id}>
                  {app.candidate_name} - {app.requisition_title} ({app.application_id})
                </option>
              ))}
            </select>
            <p className="text-xs text-muted-foreground">
              Choose the candidate and position for this offer
            </p>
          </div>

          {selectedApp && (
            <div className="rounded-lg bg-muted p-4 space-y-2">
              <p className="text-sm">
                <span className="font-medium">Candidate:</span> {selectedApp.candidate_name}
              </p>
              <p className="text-sm">
                <span className="font-medium">Email:</span> {selectedApp.candidate_email}
              </p>
              <p className="text-sm">
                <span className="font-medium">Position:</span> {selectedApp.requisition_title}
              </p>
              <p className="text-sm">
                <span className="font-medium">Current Stage:</span> {selectedApp.current_stage_name}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Position Details */}
      <Card>
        <CardHeader>
          <CardTitle>Position Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Job Title *</label>
              <Input
                name="title"
                required
                defaultValue={selectedApp?.requisition_title || ''}
                placeholder="e.g. Senior Software Engineer"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Job Level *</label>
              <select
                name="level"
                required
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="">-- Select level --</option>
                {jobLevels.map((level: any) => (
                  <option key={level.id} value={level.id}>
                    {level.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Department *</label>
              <select
                name="department"
                required
                defaultValue={selectedApp?.department_id || ''}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="">-- Select department --</option>
                {departments.map((dept: any) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Reports To</label>
              <select
                name="reporting_to"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="">-- Select manager --</option>
                {managers.map((mgr: any) => (
                  <option key={mgr.id} value={mgr.id}>
                    {mgr.user_name} - {mgr.title}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Compensation */}
      <Card>
        <CardHeader>
          <CardTitle>Compensation Package</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Base Salary *</label>
              <Input
                type="number"
                name="base_salary"
                required
                step="0.01"
                placeholder="150000"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Salary Frequency *</label>
              <select
                name="salary_frequency"
                required
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="annual">Annual</option>
                <option value="hourly">Hourly</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Currency</label>
              <select
                name="salary_currency"
                defaultValue="ZAR"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="ZAR">ZAR</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Performance Bonus</label>
              <Input
                type="number"
                name="bonus"
                step="0.01"
                placeholder="0"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Sign-on Bonus</label>
              <Input
                type="number"
                name="sign_on_bonus"
                step="0.01"
                placeholder="0"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Relocation Package</label>
              <Input
                type="number"
                name="relocation"
                step="0.01"
                placeholder="0"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Equity/Stock Options</label>
            <Input
              name="equity"
              placeholder="e.g. 10,000 RSUs vesting over 4 years"
            />
          </div>
        </CardContent>
      </Card>

      {/* Dates */}
      <Card>
        <CardHeader>
          <CardTitle>Important Dates</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Start Date *</label>
              <Input
                type="date"
                name="start_date"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Expiration Date *</label>
              <Input
                type="date"
                name="expiration_date"
                required
              />
              <p className="text-xs text-muted-foreground">
                Candidate must respond by this date
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notes */}
      <Card>
        <CardHeader>
          <CardTitle>Additional Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <textarea
            name="notes"
            rows={4}
            placeholder="Internal notes about this offer..."
            className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          />
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-4">
        <Button
          type="button"
          variant="outline"
          onClick={() => router.back()}
          disabled={loading}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating Offer...' : 'Create Offer'}
        </Button>
      </div>
    </form>
  )
}
