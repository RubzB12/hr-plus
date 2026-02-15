import type { Metadata } from 'next'
import { getProfile } from '@/lib/dal'
import type { UserProfile } from '@/types/api'
import { ProfileForm } from './profile-form'

export const metadata: Metadata = {
  title: 'My Profile',
}

export default async function ProfilePage() {
  const profile: UserProfile = await getProfile()

  return (
    <div>
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <svg className="h-6 w-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Profile</h1>
          <p className="mt-2 text-muted-foreground">
            Keep your profile up to date to improve your chances with recruiters
          </p>
        </div>
      </div>

      {/* Profile Form */}
      <div className="mt-8">
        <ProfileForm profile={profile} />
      </div>
    </div>
  )
}
