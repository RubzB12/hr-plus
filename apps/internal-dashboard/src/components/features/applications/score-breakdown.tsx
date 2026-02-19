import { AlertCircle, CheckCircle2, BarChart3 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { CandidateScore, CriterionBreakdownItem } from '@/types/scoring'

interface ScoreBarProps {
  score: number | null
  label: string
}

function ScoreBar({ score, label }: ScoreBarProps) {
  const width = score != null ? `${score}%` : '0%'
  const barColor =
    score == null
      ? 'bg-muted'
      : score >= 80
        ? 'bg-green-500'
        : score >= 60
          ? 'bg-blue-500'
          : score >= 40
            ? 'bg-yellow-500'
            : 'bg-red-500'

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium tabular-nums">
          {score != null ? `${score}/100` : '—'}
        </span>
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width }}
        />
      </div>
    </div>
  )
}

function CriterionRow({ item }: { item: CriterionBreakdownItem }) {
  const pct = Math.round(item.factor * 100)
  const met = item.factor >= 1.0
  const partiallyMet = item.factor > 0 && item.factor < 1.0

  const typeLabel: Record<string, string> = {
    skill: 'Skill',
    experience_years: 'Experience',
    education: 'Education',
    job_title: 'Job Title',
  }

  return (
    <div className="flex items-start justify-between gap-2 py-1.5 border-b last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          {met ? (
            <CheckCircle2 className="h-3 w-3 text-green-600 shrink-0" />
          ) : item.is_required ? (
            <AlertCircle className="h-3 w-3 text-red-500 shrink-0" />
          ) : (
            <div className="h-3 w-3 rounded-full border-2 border-muted-foreground shrink-0" />
          )}
          <span className="text-xs font-medium truncate">{item.value || '—'}</span>
          <span className="text-[10px] text-muted-foreground">
            ({typeLabel[item.criterion_type] ?? item.criterion_type})
          </span>
          {item.is_required && (
            <span className="text-[10px] text-red-600 font-medium">Required</span>
          )}
        </div>
        <p className="text-[10px] text-muted-foreground pl-[18px] mt-0.5 truncate">
          {item.detail}
        </p>
      </div>
      <div className="text-right shrink-0">
        <span
          className={`text-xs font-medium tabular-nums ${
            met
              ? 'text-green-600'
              : partiallyMet
                ? 'text-yellow-600'
                : 'text-red-600'
          }`}
        >
          {pct}%
        </span>
        <p className="text-[10px] text-muted-foreground">w:{item.weight}</p>
      </div>
    </div>
  )
}

interface ScoreBreakdownProps {
  score: CandidateScore
}

export function ScoreBreakdown({ score }: ScoreBreakdownProps) {
  const criteriaItems = score.profile_breakdown?.items ?? []

  const finalLabel =
    score.final_score != null ? String(score.final_score) : '—'

  const finalColor =
    score.final_score == null
      ? 'text-muted-foreground'
      : score.final_score >= 80
        ? 'text-green-600'
        : score.final_score >= 60
          ? 'text-blue-600'
          : score.final_score >= 40
            ? 'text-yellow-600'
            : 'text-red-600'

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <BarChart3 className="h-4 w-4" />
          Candidate Score
          <span className={`ml-auto text-2xl font-bold tabular-nums ${finalColor}`}>
            {finalLabel}
            {score.final_score != null && (
              <span className="text-sm font-normal text-muted-foreground">/100</span>
            )}
          </span>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {!score.meets_required_criteria && (
          <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2">
            <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
            <p className="text-xs text-red-700">
              Does not meet required criteria — score capped at 40
            </p>
          </div>
        )}

        <div className="space-y-3">
          <ScoreBar score={score.profile_score} label="Profile Match (50%)" />
          <ScoreBar score={score.interview_score} label="Interview (35%)" />
          <ScoreBar score={score.assessment_score} label="Assessment (15%)" />
        </div>

        {criteriaItems.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide mb-2">
              Criteria Breakdown
            </p>
            <div>
              {criteriaItems.map((item) => (
                <CriterionRow key={item.criterion_id} item={item} />
              ))}
            </div>
          </div>
        )}

        {criteriaItems.length === 0 && score.profile_score == null && (
          <p className="text-xs text-muted-foreground text-center py-2">
            No scoring criteria configured for this requisition.
          </p>
        )}

        <p className="text-[10px] text-muted-foreground text-right">
          v{score.scoring_version} · scored {new Date(score.scored_at).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  )
}
