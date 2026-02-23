import Link from 'next/link'
import type { JobMatchScore } from '@/types/api'

interface Props {
  matchScore: JobMatchScore
}

function ScoreRing({ score }: { score: number }) {
  const radius = 28
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  const color =
    score >= 75 ? '#16a34a' : score >= 50 ? '#ca8a04' : '#dc2626'

  return (
    <svg viewBox="0 0 72 72" className="h-16 w-16 -rotate-90">
      <circle cx="36" cy="36" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="6" />
      <circle
        cx="36"
        cy="36"
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth="6"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
      />
    </svg>
  )
}

export function MatchScorePanel({ matchScore }: Props) {
  if (matchScore.overall_score === null) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-gray-900">Your Match</h3>
        <p className="mt-2 text-sm text-gray-500">
          {matchScore.message ?? 'No criteria defined for this job.'}
        </p>
        <Link href="/dashboard/profile" className="mt-2 inline-block text-sm text-blue-600 hover:underline">
          Complete your profile →
        </Link>
      </div>
    )
  }

  const score = matchScore.overall_score
  const scoreLabel = score >= 75 ? 'Strong match' : score >= 50 ? 'Partial match' : 'Low match'
  const scoreColor = score >= 75 ? 'text-green-700' : score >= 50 ? 'text-yellow-700' : 'text-red-700'

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-gray-900">Your Match</h3>

      <div className="mt-3 flex items-center gap-4">
        <div className="relative flex h-16 w-16 items-center justify-center">
          <ScoreRing score={score} />
          <span className="absolute text-sm font-bold text-gray-900">{score}%</span>
        </div>
        <div>
          <p className={`text-sm font-semibold ${scoreColor}`}>{scoreLabel}</p>
          {!matchScore.meets_required_criteria && (
            <p className="mt-0.5 text-xs text-orange-600">Missing required criteria</p>
          )}
        </div>
      </div>

      {matchScore.skills_matched.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-medium text-gray-700">Matched skills</p>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {matchScore.skills_matched.map(skill => (
              <span key={skill} className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {matchScore.skills_missing.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-medium text-gray-700">Missing skills</p>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {matchScore.skills_missing.map(skill => (
              <span key={skill} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-3 space-y-1">
        <div className="flex items-center gap-2 text-xs text-gray-600">
          {matchScore.experience_match ? (
            <span className="text-green-600">✓</span>
          ) : (
            <span className="text-red-500">✗</span>
          )}
          Experience requirement
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-600">
          {matchScore.education_match ? (
            <span className="text-green-600">✓</span>
          ) : (
            <span className="text-red-500">✗</span>
          )}
          Education requirement
        </div>
      </div>

      {matchScore.skills_missing.length > 0 && (
        <Link
          href="/dashboard/profile#skills"
          className="mt-3 inline-block text-xs text-blue-600 hover:underline"
        >
          Add missing skills to your profile →
        </Link>
      )}
    </div>
  )
}
