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
      <h1 className="text-2xl font-bold">My Profile</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Keep your profile up to date to improve your chances with recruiters.
      </p>
      <div className="mt-8">
        <ProfileForm profile={profile} />
      </div>
    </div>
  )
}
