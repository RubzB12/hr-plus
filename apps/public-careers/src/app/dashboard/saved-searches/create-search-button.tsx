'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { createSavedSearchAction } from './actions'
import type { SearchParams } from '@/types/api'

interface CreateSearchButtonProps {
  variant?: 'default' | 'outline'
}

export function CreateSearchButton({ variant = 'outline' }: CreateSearchButtonProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [isOpen, setIsOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    keywords: searchParams.get('search') || '',
    department: searchParams.get('department') || '',
    location_city: searchParams.get('location') || '',
    employment_type: searchParams.get('employment_type') || '',
    remote_policy: searchParams.get('remote_policy') || '',
    alert_frequency: 'daily',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const search_params: SearchParams = {}

      if (formData.keywords) search_params.keywords = formData.keywords
      if (formData.department) search_params.department = formData.department
      if (formData.location_city) search_params.location_city = formData.location_city
      if (formData.employment_type) search_params.employment_type = formData.employment_type
      if (formData.remote_policy) search_params.remote_policy = formData.remote_policy

      const result = await createSavedSearchAction({
        name: formData.name,
        search_params,
        alert_frequency: formData.alert_frequency,
      })

      if (result.success) {
        setIsOpen(false)
        router.refresh()
      } else {
        alert(result.error || 'Failed to create saved search. Please try again.')
      }
    } catch (error) {
      console.error('Failed to create saved search:', error)
      alert('Failed to create saved search. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const buttonClass =
    variant === 'default'
      ? 'inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90'
      : 'inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-muted'

  return (
    <>
      <button onClick={() => setIsOpen(true)} className={buttonClass}>
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Create Saved Search
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Create Saved Search</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-lg p-1 transition-colors hover:bg-muted"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium mb-1.5">
                  Search Name <span className="text-destructive">*</span>
                </label>
                <input
                  id="name"
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Senior Python Jobs in SF"
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Keywords */}
              <div>
                <label htmlFor="keywords" className="block text-sm font-medium mb-1.5">
                  Keywords
                </label>
                <input
                  id="keywords"
                  type="text"
                  value={formData.keywords}
                  onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                  placeholder="Job title, skills, etc."
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Department */}
              <div>
                <label htmlFor="department" className="block text-sm font-medium mb-1.5">
                  Department
                </label>
                <input
                  id="department"
                  type="text"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  placeholder="Engineering, Marketing, etc."
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Location */}
              <div>
                <label htmlFor="location_city" className="block text-sm font-medium mb-1.5">
                  Location
                </label>
                <input
                  id="location_city"
                  type="text"
                  value={formData.location_city}
                  onChange={(e) => setFormData({ ...formData, location_city: e.target.value })}
                  placeholder="City name"
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Employment Type */}
              <div>
                <label htmlFor="employment_type" className="block text-sm font-medium mb-1.5">
                  Employment Type
                </label>
                <select
                  id="employment_type"
                  value={formData.employment_type}
                  onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">Any</option>
                  <option value="full_time">Full-time</option>
                  <option value="part_time">Part-time</option>
                  <option value="contract">Contract</option>
                  <option value="internship">Internship</option>
                </select>
              </div>

              {/* Remote Policy */}
              <div>
                <label htmlFor="remote_policy" className="block text-sm font-medium mb-1.5">
                  Work Mode
                </label>
                <select
                  id="remote_policy"
                  value={formData.remote_policy}
                  onChange={(e) => setFormData({ ...formData, remote_policy: e.target.value })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">Any</option>
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="onsite">On-site</option>
                </select>
              </div>

              {/* Alert Frequency */}
              <div>
                <label htmlFor="alert_frequency" className="block text-sm font-medium mb-1.5">
                  Alert Frequency <span className="text-destructive">*</span>
                </label>
                <select
                  id="alert_frequency"
                  required
                  value={formData.alert_frequency}
                  onChange={(e) => setFormData({ ...formData, alert_frequency: e.target.value })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="instant">Instant (as soon as new jobs are posted)</option>
                  <option value="daily">Daily (morning digest)</option>
                  <option value="weekly">Weekly (Monday mornings)</option>
                  <option value="never">Never (no alerts, just save criteria)</option>
                </select>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !formData.name}
                  className="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90 disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Create Search'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
