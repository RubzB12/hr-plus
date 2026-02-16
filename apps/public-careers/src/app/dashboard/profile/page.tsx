import type { Metadata } from 'next'
import { getProfile } from '@/lib/dal'
import type { CandidateProfile } from '@/types/api'
import { ProfileForm } from './profile-form'
import { ResumeUpload } from '@/components/features/profile/resume-upload'
import { WorkExperienceSection } from '@/components/features/profile/work-experience-section'
import { EducationSection } from '@/components/features/profile/education-section'
import { SkillsSection } from '@/components/features/profile/skills-section'
import { ProfileCompletionCard } from '@/components/features/profile/profile-completion-card'

export const metadata: Metadata = {
  title: 'My Profile',
}

export default async function ProfilePage() {
  const profile: CandidateProfile = await getProfile()

  return (
    <div className="space-y-8">
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
            Build a comprehensive profile to stand out to recruiters
          </p>
        </div>
      </div>

      {/* Profile Completion Card */}
      {profile.completion_details.percentage < 100 && (
        <ProfileCompletionCard completionDetails={profile.completion_details} />
      )}

      {/* Resume Upload Section */}
      <div id="resume" className="rounded-xl border border-border bg-card p-6 shadow-sm scroll-mt-20">
        <div className="flex items-center gap-2 mb-5">
          <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h2 className="text-lg font-semibold">Resume</h2>
        </div>
        <ResumeUpload currentResumeUrl={profile.resume_file} />
      </div>

      {/* Basic Information Section */}
      <div id="basic-info" className="scroll-mt-20">
        <ProfileForm profile={profile} />
      </div>

      {/* Work Experience Section */}
      <div id="experience" className="rounded-xl border border-border bg-card p-6 shadow-sm scroll-mt-20">
        <div className="flex items-center gap-2 mb-5">
          <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <WorkExperienceSection experiences={profile.experiences || []} />
      </div>

      {/* Education Section */}
      <div id="education" className="rounded-xl border border-border bg-card p-6 shadow-sm scroll-mt-20">
        <div className="flex items-center gap-2 mb-5">
          <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
        <EducationSection education={profile.education || []} />
      </div>

      {/* Skills Section */}
      <div id="skills" className="rounded-xl border border-border bg-card p-6 shadow-sm scroll-mt-20">
        <div className="flex items-center gap-2 mb-5">
          <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <SkillsSection skills={profile.skills || []} />
      </div>
    </div>
  )
}
