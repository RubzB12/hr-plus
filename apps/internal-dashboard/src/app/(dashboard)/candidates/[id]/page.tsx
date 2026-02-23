import { notFound } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Mail, Phone, MapPin, Globe, Linkedin, FileText, Briefcase, GraduationCap, Award, Calendar, Clock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getCandidateDetail } from '@/lib/dal'

export const metadata = {
  title: 'Candidate Profile — HR-Plus',
}

interface CandidateDetailPageProps {
  params: Promise<{ id: string }>
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    year: 'numeric',
  })
}

/** Allow only http/https URLs to prevent javascript: XSS injection. */
function sanitizeUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined
  try {
    const parsed = new URL(url)
    if (parsed.protocol === 'https:' || parsed.protocol === 'http:') return url
  } catch {
    // Invalid URL — drop it
  }
  return undefined
}

/** Build a safe mailto: href — rejects values that aren't valid email addresses. */
function safeMailto(email: string | null | undefined): string {
  if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return `mailto:${email}`
  return '#'
}

/** Build a safe tel: href — strips any character that isn't a valid phone symbol. */
function safeTel(phone: string | null | undefined): string {
  const sanitized = (phone ?? '').replace(/[^0-9+\-().# ]/g, '')
  return sanitized ? `tel:${sanitized}` : '#'
}

export default async function CandidateDetailPage({ params }: CandidateDetailPageProps) {
  const { id } = await params

  let candidate
  try {
    candidate = await getCandidateDetail(id)
  } catch {
    notFound()
  }

  const fullName = `${candidate.user.first_name} ${candidate.user.last_name}`
  const currentRole = candidate.experiences?.[0]
  const totalExperience = candidate.experiences?.reduce((sum: number, exp: any) => {
    if (!exp.end_date && exp.start_date) {
      const start = new Date(exp.start_date)
      const now = new Date()
      return sum + (now.getFullYear() - start.getFullYear())
    }
    if (exp.start_date && exp.end_date) {
      const start = new Date(exp.start_date)
      const end = new Date(exp.end_date)
      return sum + (end.getFullYear() - start.getFullYear())
    }
    return sum
  }, 0) || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/candidates" className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Candidates
          </Link>
        </Button>
      </div>

      {/* Profile Overview */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start gap-6">
            <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <span className="text-3xl font-bold text-primary">
                {candidate.user.first_name.charAt(0)}{candidate.user.last_name.charAt(0)}
              </span>
            </div>

            <div className="flex-1">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-3xl font-bold">{fullName}</h1>
                  {currentRole && (
                    <p className="text-lg text-muted-foreground mt-1">
                      {currentRole.title} at {currentRole.company_name}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-sm text-muted-foreground">Profile Completeness</div>
                  <div className="text-2xl font-bold">{candidate.profile_completeness}%</div>
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2 mb-4">
                <div className="flex items-center gap-2 text-sm">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <a href={safeMailto(candidate.user.email)} className="hover:underline">
                    {candidate.user.email}
                  </a>
                </div>

                {candidate.phone && (
                  <div className="flex items-center gap-2 text-sm">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <a href={safeTel(candidate.phone)} className="hover:underline">
                      {candidate.phone}
                    </a>
                  </div>
                )}

                {candidate.location_city && (
                  <div className="flex items-center gap-2 text-sm">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    <span>{candidate.location_city}, {candidate.location_country}</span>
                  </div>
                )}

                {candidate.work_authorization && (
                  <div className="flex items-center gap-2 text-sm">
                    <Award className="h-4 w-4 text-muted-foreground" />
                    <span>{candidate.work_authorization.replace('_', ' ')}</span>
                  </div>
                )}

                {candidate.linkedin_url && (
                  <div className="flex items-center gap-2 text-sm">
                    <Linkedin className="h-4 w-4 text-muted-foreground" />
                    <a
                      href={sanitizeUrl(candidate.linkedin_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline text-primary"
                    >
                      LinkedIn Profile
                    </a>
                  </div>
                )}

                {candidate.portfolio_url && (
                  <div className="flex items-center gap-2 text-sm">
                    <Globe className="h-4 w-4 text-muted-foreground" />
                    <a
                      href={sanitizeUrl(candidate.portfolio_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline text-primary"
                    >
                      Portfolio
                    </a>
                  </div>
                )}
              </div>

              {candidate.resume_file && (
                <Button asChild variant="outline">
                  <a href={sanitizeUrl(candidate.resume_file)} target="_blank" rel="noopener noreferrer">
                    <FileText className="h-4 w-4 mr-2" />
                    View Resume
                  </a>
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Skills */}
      {candidate.skills && candidate.skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5" />
              Skills & Expertise
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {candidate.skills.map((skill: any) => (
                <Badge key={skill.id} variant="secondary" className="text-sm py-1.5 px-3">
                  {skill.name}
                  {skill.years_experience && (
                    <span className="ml-2 text-xs text-muted-foreground">
                      {skill.years_experience}y
                    </span>
                  )}
                  {skill.proficiency && skill.proficiency !== 'intermediate' && (
                    <span className="ml-2 text-xs text-muted-foreground">
                      • {skill.proficiency}
                    </span>
                  )}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Work Experience */}
      {candidate.experiences && candidate.experiences.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase className="h-5 w-5" />
              Work Experience ({totalExperience}+ years)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {candidate.experiences.map((exp: any, idx: number) => (
                <div key={exp.id} className={idx > 0 ? 'border-t pt-6' : ''}>
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-semibold text-lg">{exp.title}</h3>
                      <p className="text-muted-foreground">{exp.company_name}</p>
                    </div>
                    <div className="text-sm text-muted-foreground text-right">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(exp.start_date)} - {exp.end_date ? formatDate(exp.end_date) : 'Present'}
                      </div>
                      {exp.location && (
                        <div className="flex items-center gap-1 mt-1">
                          <MapPin className="h-3 w-3" />
                          {exp.location}
                        </div>
                      )}
                    </div>
                  </div>
                  {exp.description && (
                    <p className="text-sm text-muted-foreground whitespace-pre-wrap mt-2">
                      {exp.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Education */}
      {candidate.education && candidate.education.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GraduationCap className="h-5 w-5" />
              Education
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {candidate.education.map((edu: any) => (
                <div key={edu.id} className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold">{edu.degree} in {edu.field_of_study}</h3>
                    <p className="text-sm text-muted-foreground">{edu.institution}</p>
                    {edu.gpa && (
                      <p className="text-xs text-muted-foreground mt-1">GPA: {edu.gpa}</p>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {edu.graduation_date ? formatDate(edu.graduation_date) : 'In Progress'}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Candidate Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Candidate Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            <p>Joined: {new Date(candidate.created_at).toLocaleDateString('en-US', {
              month: 'long',
              day: 'numeric',
              year: 'numeric'
            })}</p>
            <p className="mt-2">
              Total Applications: <span className="font-medium text-foreground">0</span>
            </p>
            <p>
              Active Applications: <span className="font-medium text-foreground">0</span>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
