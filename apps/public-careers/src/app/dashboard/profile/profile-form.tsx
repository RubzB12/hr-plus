'use client'

import { useActionState } from 'react'
import { updateProfileAction, type ProfileState } from './actions'
import type { CandidateProfile } from '@/types/api'

const initialState: ProfileState = { success: false }

export function ProfileForm({ profile }: { profile: CandidateProfile }) {
  const [state, formAction, isPending] = useActionState(
    updateProfileAction,
    initialState
  )

  const completeness = profile.profile_completeness ?? 0

  return (
    <div className="space-y-6">
      {/* Profile Completeness */}
      <div className="rounded-xl border border-border bg-gradient-to-br from-primary/5 to-primary/10 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold">Profile Completeness</span>
              <span className="text-sm font-bold text-primary">{completeness}%</span>
            </div>
          </div>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/50">
          <div
            className="h-full rounded-full bg-primary shadow-sm transition-all duration-300"
            style={{ width: `${completeness}%` }}
          />
        </div>
        {completeness < 100 && (
          <p className="mt-3 text-xs text-primary/80">
            {completeness < 60
              ? 'Complete your profile to stand out to recruiters'
              : completeness < 80
              ? 'You\'re almost there! Fill in the remaining fields'
              : 'Just a few more fields to go'}
          </p>
        )}
      </div>

      <form action={formAction} className="space-y-6">
        {/* Success/Error Message */}
        {state.message && (
          <div
            className={`rounded-xl border p-4 text-sm ${
              state.success
                ? 'border-green-200 bg-green-50 text-green-700'
                : 'border-red-200 bg-red-50 text-red-700'
            }`}
          >
            <div className="flex items-start gap-3">
              {state.success ? (
                <svg className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ) : (
                <svg className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
              <span>{state.message}</span>
            </div>
          </div>
        )}

        {/* Personal Information */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-5">
            <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <h2 className="text-lg font-semibold">Personal Information</h2>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium mb-1.5">
                  First name *
                </label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  required
                  defaultValue={profile.user.first_name}
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
                {state.errors?.first_name && (
                  <p className="mt-1.5 text-xs text-red-600">
                    {state.errors.first_name[0]}
                  </p>
                )}
              </div>
              <div>
                <label htmlFor="last_name" className="block text-sm font-medium mb-1.5">
                  Last name *
                </label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  required
                  defaultValue={profile.user.last_name}
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
                {state.errors?.last_name && (
                  <p className="mt-1.5 text-xs text-red-600">
                    {state.errors.last_name[0]}
                  </p>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-1.5">
                Email address
              </label>
              <input
                id="email"
                type="email"
                disabled
                value={profile.user.email}
                className="block w-full rounded-lg border border-border bg-muted px-3 py-2.5 text-sm text-muted-foreground cursor-not-allowed"
              />
              <p className="mt-1.5 text-xs text-muted-foreground">
                Email cannot be changed. Contact support if you need to update it.
              </p>
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium mb-1.5">
                Phone number
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                placeholder="+27 82 123 4567"
                defaultValue={profile.phone}
                className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
              {state.errors?.phone && (
                <p className="mt-1.5 text-xs text-red-600">{state.errors.phone[0]}</p>
              )}
            </div>
          </div>
        </div>

        {/* Location */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-5">
            <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <h2 className="text-lg font-semibold">Location</h2>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="location_city" className="block text-sm font-medium mb-1.5">
                  City
                </label>
                <input
                  id="location_city"
                  name="location_city"
                  type="text"
                  placeholder="Durban"
                  defaultValue={profile.location_city}
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
              <div>
                <label htmlFor="location_country" className="block text-sm font-medium mb-1.5">
                  Country
                </label>
                <input
                  id="location_country"
                  name="location_country"
                  type="text"
                  placeholder="South Africa"
                  defaultValue={profile.location_country}
                  className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
            </div>

            <div>
              <label htmlFor="work_authorization" className="block text-sm font-medium mb-1.5">
                Work authorization
              </label>
              <input
                id="work_authorization"
                name="work_authorization"
                type="text"
                placeholder="e.g. SA Citizen, Work Permit, Permanent Resident"
                defaultValue={profile.work_authorization}
                className="block w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
              <p className="mt-1.5 text-xs text-muted-foreground">
                Specifying your work authorization helps recruiters match you with eligible positions
              </p>
            </div>
          </div>
        </div>

        {/* Online Presence */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-5">
            <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
            <h2 className="text-lg font-semibold">Online Presence</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label htmlFor="linkedin_url" className="block text-sm font-medium mb-1.5">
                LinkedIn Profile
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2">
                  <svg className="h-4 w-4 text-muted-foreground" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                  </svg>
                </div>
                <input
                  id="linkedin_url"
                  name="linkedin_url"
                  type="url"
                  placeholder="https://linkedin.com/in/yourprofile"
                  defaultValue={profile.linkedin_url}
                  className="block w-full rounded-lg border border-border bg-background pl-10 pr-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
              {state.errors?.linkedin_url && (
                <p className="mt-1.5 text-xs text-red-600">
                  {state.errors.linkedin_url[0]}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="portfolio_url" className="block text-sm font-medium mb-1.5">
                Portfolio / Website
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2">
                  <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                </div>
                <input
                  id="portfolio_url"
                  name="portfolio_url"
                  type="url"
                  placeholder="https://yourportfolio.com"
                  defaultValue={profile.portfolio_url}
                  className="block w-full rounded-lg border border-border bg-background pl-10 pr-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
                />
              </div>
              {state.errors?.portfolio_url && (
                <p className="mt-1.5 text-xs text-red-600">
                  {state.errors.portfolio_url[0]}
                </p>
              )}
              <p className="mt-1.5 text-xs text-muted-foreground">
                Showcase your work with a personal website or portfolio
              </p>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-between rounded-xl border border-border bg-muted/50 p-4">
          <p className="text-sm text-muted-foreground">
            Make sure all information is accurate before saving
          </p>
          <button
            type="submit"
            disabled={isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-primary/90 hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isPending ? (
              <>
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Saving...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Save Changes
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
