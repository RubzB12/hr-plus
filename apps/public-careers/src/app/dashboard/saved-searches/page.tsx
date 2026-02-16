import { Metadata } from 'next'
import Link from 'next/link'
import { getSavedSearches } from '@/lib/dal'
import type { SavedSearch } from '@/types/api'
import { SavedSearchCard } from './saved-search-card'
import { CreateSearchButton } from './create-search-button'

export const metadata: Metadata = {
  title: 'Saved Searches',
  description: 'Manage your saved job searches and email alerts',
}

export default async function SavedSearchesPage() {
  let savedSearches: SavedSearch[] = []
  let error: string | null = null

  try {
    const response = await getSavedSearches()
    savedSearches = Array.isArray(response) ? response : response.results || []
  } catch (e) {
    error = 'Failed to load saved searches. Please try again later.'
    console.error(e)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Saved Searches</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Get notified when new jobs match your criteria
          </p>
        </div>
        <CreateSearchButton />
      </div>

      {/* Info Banner */}
      <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
        <div className="flex items-start gap-3">
          <svg
            className="h-5 w-5 flex-shrink-0 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-medium">How it works</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Save your job search criteria and choose how often you want to receive email alerts.
              We'll notify you when new positions match your preferences.
            </p>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Saved Searches List */}
      {savedSearches.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {savedSearches.map((search) => (
            <SavedSearchCard key={search.id} savedSearch={search} />
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="rounded-lg border border-dashed border-border bg-muted/30 px-6 py-12 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <svg
              className="h-6 w-6 text-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold">No saved searches yet</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Create your first saved search to get email alerts for matching jobs.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <CreateSearchButton variant="default" />
            <Link
              href="/jobs"
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
            >
              Browse Jobs
            </Link>
          </div>
        </div>
      )}

      {/* Help Section */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h3 className="font-semibold">Tips for effective job alerts</h3>
        <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span>
              Use specific keywords to match your ideal role (e.g., "Senior Python Engineer" vs "Developer")
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span>
              Set multiple saved searches for different types of roles you're interested in
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span>
              Choose "Instant" alerts for highly competitive roles, "Daily" for general searches
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary">•</span>
            <span>
              You can pause alerts anytime without deleting your search criteria
            </span>
          </li>
        </ul>
      </div>
    </div>
  )
}
