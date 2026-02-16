'use client'

import Link from 'next/link'
import type { ProfileCompletionDetails } from '@/types/api'

interface ProfileCompletionCardProps {
  completionDetails: ProfileCompletionDetails
}

export function ProfileCompletionCard({ completionDetails }: ProfileCompletionCardProps) {
  const { percentage, completed_count, total_items, missing_items } = completionDetails

  // Determine color based on completion percentage
  const getProgressColor = () => {
    if (percentage >= 90) return 'bg-green-600'
    if (percentage >= 70) return 'bg-blue-600'
    if (percentage >= 50) return 'bg-yellow-600'
    return 'bg-orange-600'
  }

  const getProgressTextColor = () => {
    if (percentage >= 90) return 'text-green-600'
    if (percentage >= 70) return 'text-blue-600'
    if (percentage >= 50) return 'text-yellow-600'
    return 'text-orange-600'
  }

  const getPriorityBadgeClass = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 text-red-700 border-red-200'
      case 'high':
        return 'bg-orange-100 text-orange-700 border-orange-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const getActionLink = (field: string) => {
    // Map fields to the appropriate section of the profile page
    switch (field) {
      case 'first_name':
      case 'last_name':
      case 'phone':
      case 'location':
      case 'work_authorization':
      case 'links':
        return '/dashboard/profile#basic-info'
      case 'resume':
        return '/dashboard/profile#resume'
      case 'work_experience':
        return '/dashboard/profile#experience'
      case 'education':
        return '/dashboard/profile#education'
      case 'skills':
        return '/dashboard/profile#skills'
      default:
        return '/dashboard/profile'
    }
  }

  // If profile is complete, show success message
  if (percentage === 100) {
    return (
      <div className="rounded-xl border border-green-200 bg-gradient-to-br from-green-50 to-green-100/50 p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-green-600">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-green-900">Profile Complete!</h3>
            <p className="mt-1 text-sm text-green-700">
              Your profile is fully optimized. Recruiters can now see your complete professional story.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold">Complete Your Profile</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {completed_count} of {total_items} items completed
          </p>
        </div>
        <div className="text-right">
          <div className={`text-3xl font-bold ${getProgressTextColor()}`}>{percentage}%</div>
          <div className="text-xs text-muted-foreground">Complete</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full transition-all duration-500 ${getProgressColor()}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Missing Items */}
      {missing_items.length > 0 && (
        <div className="mt-6 space-y-3">
          <h4 className="text-sm font-medium">Complete these items to stand out:</h4>
          {missing_items.map((item) => (
            <Link
              key={item.field}
              href={getActionLink(item.field)}
              className="block rounded-lg border border-border bg-background p-4 transition-all hover:border-primary/50 hover:shadow-md"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-sm">{item.action}</p>
                    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium border ${getPriorityBadgeClass(item.priority)}`}>
                      {item.priority}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-muted-foreground">{item.label}</p>
                </div>
                <svg className="h-5 w-5 shrink-0 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Call to Action */}
      {percentage < 80 && (
        <div className="mt-6 rounded-lg bg-primary/5 p-4 border border-primary/20">
          <div className="flex items-start gap-3">
            <svg className="h-5 w-5 shrink-0 text-primary mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1 text-sm">
              <p className="font-medium text-foreground">
                Complete your profile to increase your chances of getting hired
              </p>
              <p className="mt-1 text-muted-foreground">
                Profiles with 80%+ completion get 3x more interview requests.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
