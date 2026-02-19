'use client'

import { useState, useEffect } from 'react'
import { Search, Filter, User, MapPin, Briefcase, Mail, Phone, FileText } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface Candidate {
  id: string
  user: {
    id: string
    email: string
    first_name: string
    last_name: string
  }
  phone: string
  location_city: string
  location_country: string
  work_authorization: string
  resume_file: string | null
  linkedin_url: string
  portfolio_url: string
  profile_completeness: number
  experiences: any[]
  education: any[]
  skills: Array<{
    id: string
    name: string
    proficiency: string
    years_experience: number | null
  }>
  created_at: string
}

interface SearchFilters {
  q: string
  skills: string
  location_city: string
  location_country: string
  experience_min: string
  experience_max: string
  work_authorization: string
  source: string
  salary_max: string
}

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState<SearchFilters>({
    q: '',
    skills: '',
    location_city: '',
    location_country: '',
    experience_min: '',
    experience_max: '',
    work_authorization: '',
    source: '',
    salary_max: '',
  })

  const searchCandidates = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()

      // Only add non-empty filters
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value)
      })

      const response = await fetch(`/api/candidates/search?${params}`)

      if (!response.ok) throw new Error('Search failed')

      const data = await response.json()
      setCandidates(data.results || [])
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Auto-search on component mount
    searchCandidates()
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    searchCandidates()
  }

  const resetFilters = () => {
    setFilters({
      q: '',
      skills: '',
      location_city: '',
      location_country: '',
      experience_min: '',
      experience_max: '',
      work_authorization: '',
      source: '',
      salary_max: '',
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Candidate Search</h1>
          <p className="text-muted-foreground mt-2">
            Search and discover talent using AI-powered semantic search
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2"
        >
          <Filter className="h-4 w-4" />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </Button>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch}>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by name, email, skills, or keywords..."
              value={filters.q}
              onChange={(e) => setFilters({ ...filters, q: e.target.value })}
              className="pl-10"
            />
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </Button>
        </div>
      </form>

      {/* Advanced Filters */}
      {showFilters && (
        <Card>
          <CardHeader>
            <CardTitle>Advanced Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-2">
                <label className="text-sm font-medium">Skills</label>
                <Input
                  placeholder="e.g., Python, React, AWS"
                  value={filters.skills}
                  onChange={(e) => setFilters({ ...filters, skills: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">Comma-separated</p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Location City</label>
                <Input
                  placeholder="e.g., San Francisco"
                  value={filters.location_city}
                  onChange={(e) => setFilters({ ...filters, location_city: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Work Authorization</label>
                <select
                  value={filters.work_authorization}
                  onChange={(e) => setFilters({ ...filters, work_authorization: e.target.value })}
                  className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">All</option>
                  <option value="citizen">Citizen</option>
                  <option value="permanent_resident">Permanent Resident</option>
                  <option value="work_visa">Work Visa</option>
                  <option value="student_visa">Student Visa</option>
                  <option value="requires_sponsorship">Requires Sponsorship</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Min Experience (years)</label>
                <Input
                  type="number"
                  min="0"
                  placeholder="0"
                  value={filters.experience_min}
                  onChange={(e) => setFilters({ ...filters, experience_min: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Max Experience (years)</label>
                <Input
                  type="number"
                  min="0"
                  placeholder="10"
                  value={filters.experience_max}
                  onChange={(e) => setFilters({ ...filters, experience_max: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Source</label>
                <select
                  value={filters.source}
                  onChange={(e) => setFilters({ ...filters, source: e.target.value })}
                  className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">All</option>
                  <option value="direct">Direct Application</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="indeed">Indeed</option>
                  <option value="referral">Referral</option>
                  <option value="agency">Agency</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-2 mt-4">
              <Button onClick={searchCandidates} disabled={loading}>
                Apply Filters
              </Button>
              <Button variant="outline" onClick={resetFilters}>
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      <div>
        <p className="text-sm text-muted-foreground mb-4">
          {loading ? 'Searching...' : `${candidates.length} candidates found`}
        </p>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-6">
                  <div className="h-20 bg-muted rounded"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : candidates.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No candidates found</h3>
              <p className="text-sm text-muted-foreground">
                Try adjusting your search criteria or filters
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {candidates.map((candidate) => (
              <Card key={candidate.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-3">
                      <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">
                          {candidate.user.first_name} {candidate.user.last_name}
                        </h3>
                        {candidate.experiences && candidate.experiences[0] && (
                          <p className="text-sm text-muted-foreground">
                            {candidate.experiences[0].title} at {candidate.experiences[0].company_name}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-muted-foreground">
                        Profile {candidate.profile_completeness}% complete
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Mail className="h-4 w-4" />
                      {candidate.user.email}
                    </div>
                    {candidate.phone && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Phone className="h-4 w-4" />
                        {candidate.phone}
                      </div>
                    )}
                    {candidate.location_city && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <MapPin className="h-4 w-4" />
                        {candidate.location_city}, {candidate.location_country}
                      </div>
                    )}
                  </div>

                  {/* Skills */}
                  {candidate.skills && candidate.skills.length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs font-medium text-muted-foreground mb-2">Skills</p>
                      <div className="flex flex-wrap gap-1">
                        {candidate.skills.slice(0, 5).map((skill) => (
                          <span
                            key={skill.id}
                            className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium"
                          >
                            {skill.name}
                          </span>
                        ))}
                        {candidate.skills.length > 5 && (
                          <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium">
                            +{candidate.skills.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <Button size="sm" className="flex-1" asChild>
                      <a href={`/candidates/${candidate.id}`}>View Profile</a>
                    </Button>
                    {candidate.resume_file && (
                      <Button size="sm" variant="outline" asChild>
                        <a href={candidate.resume_file} target="_blank" rel="noopener noreferrer">
                          <FileText className="h-4 w-4" />
                        </a>
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
