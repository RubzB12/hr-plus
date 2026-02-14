'use client'

import { useActionState } from 'react'
import { updateProfileAction, type ProfileState } from './actions'
import type { UserProfile } from '@/types/api'

const initialState: ProfileState = { success: false }

export function ProfileForm({ profile }: { profile: UserProfile }) {
  const [state, formAction, isPending] = useActionState(
    updateProfileAction,
    initialState
  )

  const cp = profile.candidate_profile
  const completeness = cp.profile_completeness ?? 0

  return (
    <div>
      {/* Profile completeness */}
      <div className="mb-8 rounded-lg border border-border bg-muted p-4">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">Profile completeness</span>
          <span className="text-muted-foreground">{completeness}%</span>
        </div>
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-border">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${completeness}%` }}
          />
        </div>
        {completeness < 80 && (
          <p className="mt-2 text-xs text-muted-foreground">
            Complete your profile to increase visibility with recruiters.
          </p>
        )}
      </div>

      <form action={formAction} className="space-y-6">
        {state.message && (
          <div
            className={`rounded-lg border p-3 text-sm ${
              state.success
                ? 'border-green-200 bg-green-50 text-green-700'
                : 'border-red-200 bg-red-50 text-red-700'
            }`}
          >
            {state.message}
          </div>
        )}

        <fieldset className="space-y-5">
          <legend className="text-lg font-semibold">Personal Information</legend>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="first_name" className="block text-sm font-medium">
                First name
              </label>
              <input
                id="first_name"
                name="first_name"
                type="text"
                required
                defaultValue={profile.first_name}
                className="mt-1.5 block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              />
              {state.errors?.first_name && (
                <p className="mt-1 text-xs text-red-600">
                  {state.errors.first_name[0]}
                </p>
              )}
            </div>
            <div>
              <label htmlFor="last_name" className="block text-sm font-medium">
                Last name
              </label>
              <input
                id="last_name"
                name="last_name"
                type="text"
                required
                defaultValue={profile.last_name}
                className="mt-1.5 block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              />
              {state.errors?.last_name && (
                <p className="mt-1 text-xs text-red-600">
                  {state.errors.last_name[0]}
                </p>
              )}
            </div>
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium">
              Email address
            </label>
            <input
              id="email"
              type="email"
              disabled
              value={profile.email}
              className="mt-1.5 block w-full rounded-lg border border-border bg-muted px-3 py-2 text-sm text-muted-foreground"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Email cannot be changed here.
            </p>
          </div>

          <div>
            <label htmlFor="phone" className="block text-sm font-medium">
              Phone number
            </label>
            <input
              id="phone"
              name="phone"
              type="tel"
              defaultValue={cp.phone}
              className="mt-1.5 block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            />
            {state.errors?.phone && (
              <p className="mt-1 text-xs text-red-600">{state.errors.phone[0]}</p>
            )}
          </div>
        </fieldset>

        <fieldset className="space-y-5">
          <legend className="text-lg font-semibold">Location</legend>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="location_city" className="block text-sm font-medium">
                City
              </label>
              <input
                id="location_city"
                name="location_city"
                type="text"
                defaultValue={cp.location_city}
                className="mt-1.5 block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>
            <div>
              <label htmlFor="location_country" className="block text-sm font-medium">
                Country
              </label>
              <input
                id="location_country"
                name="location_country"
                type="text"
                defaultValue={cp.location_country}
                className="mt-1.5 block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>

          <div>
            <label htmlFor="work_authorization" className="block text-sm font-medium">
              Work authorization
            </label>
            <input
              id="work_authorization"
              name="work_authorization"
              type="text"
              placeholder="e.g. US Citizen, Work Visa, etc."
              defaultValue={cp.work_authorization}
              className="mt-1.5 block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            />
          </div>
        </fieldset>

        <fieldset className="space-y-5">
          <legend className="text-lg font-semibold">Online Presence</legend>

          <div>
            <label htmlFor="linkedin_url" className="block text-sm font-medium">
              LinkedIn URL
            </label>
            <input
              id="linkedin_url"
              name="linkedin_url"
              type="url"
              placeholder="https://linkedin.com/in/yourprofile"
              defaultValue={cp.linkedin_url}
              className="mt-1.5 block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            />
            {state.errors?.linkedin_url && (
              <p className="mt-1 text-xs text-red-600">
                {state.errors.linkedin_url[0]}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="portfolio_url" className="block text-sm font-medium">
              Portfolio / Website URL
            </label>
            <input
              id="portfolio_url"
              name="portfolio_url"
              type="url"
              placeholder="https://yourportfolio.com"
              defaultValue={cp.portfolio_url}
              className="mt-1.5 block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            />
            {state.errors?.portfolio_url && (
              <p className="mt-1 text-xs text-red-600">
                {state.errors.portfolio_url[0]}
              </p>
            )}
          </div>
        </fieldset>

        <div className="flex justify-end border-t border-border pt-6">
          <button
            type="submit"
            disabled={isPending}
            className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-dark disabled:opacity-50"
          >
            {isPending ? 'Saving...' : 'Save changes'}
          </button>
        </div>
      </form>
    </div>
  )
}
