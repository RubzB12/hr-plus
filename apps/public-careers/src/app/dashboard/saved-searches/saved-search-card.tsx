'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import type { SavedSearch } from '@/types/api'
import { deleteSavedSearchAction, toggleSavedSearchAlertsAction } from './actions'

interface SavedSearchCardProps {
  savedSearch: SavedSearch
}

export function SavedSearchCard({ savedSearch }: SavedSearchCardProps) {
  const router = useRouter()
  const [isDeleting, setIsDeleting] = useState(false)
  const [isTogglingAlerts, setIsTogglingAlerts] = useState(false)
  const [isActive, setIsActive] = useState(savedSearch.is_active)

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this saved search?')) {
      return
    }

    setIsDeleting(true)
    try {
      const result = await deleteSavedSearchAction(savedSearch.id)
      if (result.success) {
        router.refresh()
      } else {
        alert(result.error || 'Failed to delete saved search. Please try again.')
        setIsDeleting(false)
      }
    } catch (error) {
      console.error('Failed to delete saved search:', error)
      alert('Failed to delete saved search. Please try again.')
      setIsDeleting(false)
    }
  }

  const handleToggleAlerts = async () => {
    setIsTogglingAlerts(true)
    try {
      const result = await toggleSavedSearchAlertsAction(savedSearch.id)
      if (result.success) {
        setIsActive(!isActive)
        router.refresh()
      } else {
        alert(result.error || 'Failed to toggle alerts. Please try again.')
      }
    } catch (error) {
      console.error('Failed to toggle alerts:', error)
      alert('Failed to toggle alerts. Please try again.')
    } finally {
      setIsTogglingAlerts(false)
    }
  }

  const formatSearchParams = () => {
    const params = savedSearch.search_params
    const parts: string[] = []

    if (params.keywords || params.search) {
      parts.push(`"${params.keywords || params.search}"`)
    }
    if (params.department) parts.push(params.department)
    if (params.location_city) parts.push(params.location_city)
    if (params.remote_policy) {
      parts.push(
        params.remote_policy === 'remote'
          ? 'Remote'
          : params.remote_policy === 'hybrid'
          ? 'Hybrid'
          : 'On-site'
      )
    }
    if (params.employment_type) {
      parts.push(params.employment_type.replace('_', ' '))
    }

    return parts.length > 0 ? parts.join(' • ') : 'All jobs'
  }

  const getFrequencyLabel = (frequency: string) => {
    const labels: Record<string, string> = {
      instant: 'Instant',
      daily: 'Daily',
      weekly: 'Weekly',
      never: 'Never',
    }
    return labels[frequency] || frequency
  }

  const getFrequencyColor = (frequency: string) => {
    const colors: Record<string, string> = {
      instant: 'bg-green-100 text-green-700 border-green-200',
      daily: 'bg-blue-100 text-blue-700 border-blue-200',
      weekly: 'bg-purple-100 text-purple-700 border-purple-200',
      never: 'bg-gray-100 text-gray-700 border-gray-200',
    }
    return colors[frequency] || colors.never
  }

  return (
    <div className="rounded-lg border border-border bg-card p-5 shadow-sm transition-all hover:shadow-md">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <h3 className="font-semibold leading-tight">{savedSearch.name}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{formatSearchParams()}</p>
        </div>

        {/* Active Status Indicator */}
        {isActive ? (
          <div className="flex h-2 w-2 items-center justify-center">
            <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500"></span>
          </div>
        ) : (
          <div className="h-2 w-2 rounded-full bg-gray-300"></div>
        )}
      </div>

      {/* Stats */}
      <div className="mt-4 flex items-center gap-4 text-sm">
        <div className="flex items-center gap-1.5">
          <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <span className="font-medium">{savedSearch.match_count}</span>
          <span className="text-muted-foreground">
            {savedSearch.match_count === 1 ? 'match' : 'matches'}
          </span>
        </div>

        <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${getFrequencyColor(savedSearch.alert_frequency)}`}>
          {getFrequencyLabel(savedSearch.alert_frequency)} alerts
        </span>
      </div>

      {/* Last Notified */}
      {savedSearch.last_notified_at && (
        <p className="mt-2 text-xs text-muted-foreground">
          Last alert: {new Date(savedSearch.last_notified_at).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
          })}
        </p>
      )}

      {/* Actions */}
      <div className="mt-4 flex items-center gap-2 border-t border-border pt-4">
        <Link
          href={`/dashboard/saved-searches/${savedSearch.id}`}
          className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          View Matches
        </Link>

        <button
          onClick={handleToggleAlerts}
          disabled={isTogglingAlerts}
          className="rounded-md border border-border bg-background p-2 transition-colors hover:bg-muted disabled:opacity-50"
          title={isActive ? 'Pause alerts' : 'Resume alerts'}
        >
          {isTogglingAlerts ? (
            <svg className="h-4 w-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          ) : isActive ? (
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ) : (
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </button>

        <button
          onClick={handleDelete}
          disabled={isDeleting}
          className="rounded-md border border-destructive/20 bg-background p-2 text-destructive transition-colors hover:bg-destructive/10 disabled:opacity-50"
          title="Delete search"
        >
          {isDeleting ? (
            <svg className="h-4 w-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          ) : (
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          )}
        </button>
      </div>
    </div>
  )
}
