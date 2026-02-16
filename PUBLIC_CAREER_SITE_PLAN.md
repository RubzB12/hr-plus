# Public Career Site - Implementation Plan

**Date:** February 16, 2026
**Status:** 🔴 In Progress
**Estimated Time:** 10-15 days

---

## Overview

The Public Career Site is a candidate-facing Next.js application that provides:
- SEO-optimized job listings
- Application submission
- Candidate portal for tracking applications
- Modern, responsive design
- Performance-optimized with Static Site Generation

---

## Architecture

### Technology Stack

**Frontend:**
- Next.js 16.1.6 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components (shared with internal dashboard)
- React Hook Form + Zod validation
- React Query for data fetching

**Backend Integration:**
- Django REST API (existing)
- Server-side rendering for SEO
- Static Site Generation for job pages
- Incremental Static Regeneration (ISR)

**Authentication:**
- Simple email/password for candidates
- Social login (Google, LinkedIn) - Phase 2
- Session-based with HttpOnly cookies

---

## Application Structure

```
apps/public-careers/
├── src/
│   ├── app/
│   │   ├── (public)/
│   │   │   ├── page.tsx                    # Homepage
│   │   │   ├── jobs/
│   │   │   │   ├── page.tsx                # Job board (SSR)
│   │   │   │   └── [slug]/
│   │   │   │       └── page.tsx            # Job detail (SSG)
│   │   │   ├── about/
│   │   │   │   └── page.tsx                # About company
│   │   │   ├── culture/
│   │   │   │   └── page.tsx                # Company culture
│   │   │   └── contact/
│   │   │       └── page.tsx                # Contact us
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   │   └── page.tsx                # Candidate login
│   │   │   ├── register/
│   │   │   │   └── page.tsx                # Candidate registration
│   │   │   ├── forgot-password/
│   │   │   │   └── page.tsx                # Password reset
│   │   │   └── reset-password/
│   │   │       └── page.tsx                # Reset confirm
│   │   ├── (candidate)/
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx                # Candidate dashboard
│   │   │   ├── applications/
│   │   │   │   ├── page.tsx                # Application list
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx            # Application detail
│   │   │   ├── profile/
│   │   │   │   └── page.tsx                # Edit profile
│   │   │   ├── interviews/
│   │   │   │   ├── page.tsx                # Upcoming interviews
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx            # Interview detail
│   │   │   └── offers/
│   │   │       ├── page.tsx                # Offers list
│   │   │       └── [id]/
│   │   │           └── page.tsx            # Offer detail
│   │   ├── apply/
│   │   │   └── [jobId]/
│   │   │       └── page.tsx                # Application form
│   │   ├── layout.tsx                       # Root layout
│   │   ├── error.tsx                        # Error boundary
│   │   ├── not-found.tsx                    # 404 page
│   │   └── global-error.tsx                 # Global error
│   ├── components/
│   │   ├── ui/                              # shadcn/ui components
│   │   ├── layouts/
│   │   │   ├── public-header.tsx            # Public site header
│   │   │   ├── public-footer.tsx            # Public site footer
│   │   │   └── candidate-sidebar.tsx        # Candidate portal sidebar
│   │   └── features/
│   │       ├── job-search/
│   │       │   ├── job-card.tsx
│   │       │   ├── job-filters.tsx
│   │       │   └── search-bar.tsx
│   │       ├── application/
│   │       │   ├── application-form.tsx
│   │       │   ├── resume-upload.tsx
│   │       │   └── screening-questions.tsx
│   │       └── candidate-dashboard/
│   │           ├── application-tracker.tsx
│   │           ├── interview-card.tsx
│   │           └── offer-card.tsx
│   ├── lib/
│   │   ├── dal.ts                           # Data Access Layer
│   │   ├── auth/
│   │   │   ├── session.ts                   # Session management
│   │   │   └── index.ts
│   │   └── utils.ts
│   ├── types/
│   │   └── api.ts                           # API types (shared)
│   ├── middleware.ts                        # Route protection
│   └── __tests__/
├── public/
│   ├── images/
│   └── favicon.ico
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
├── jest.config.js
└── playwright.config.ts
```

---

## Page Specifications

### 1. Homepage `/`
**Purpose:** Landing page showcasing company and open positions

**Features:**
- Hero section with CTA ("View Open Positions")
- Featured job listings (3-5 jobs)
- Company value propositions
- Employee testimonials
- Quick stats (employees, locations, benefits)
- SEO optimized with proper meta tags

**Rendering:** SSR with ISR (revalidate every 5 minutes)

### 2. Job Board `/jobs`
**Purpose:** Searchable list of all open positions

**Features:**
- Search bar (job title, keywords)
- Filters:
  - Department
  - Location (city, remote)
  - Job type (full-time, part-time, contract)
  - Experience level
- Sort options (date posted, relevance)
- Pagination
- Job cards with:
  - Title
  - Department
  - Location
  - Posted date
  - Salary range (if available)
  - "Apply Now" CTA

**Rendering:** SSR (always fresh data)

**API:** `GET /api/v1/jobs/?status=open`

### 3. Job Detail `/jobs/[slug]`
**Purpose:** Detailed job posting with application CTA

**Features:**
- Job title and metadata
- Full job description (rich text)
- Requirements and qualifications
- Responsibilities
- Benefits and perks
- About the team/department
- Application deadline (if set)
- "Apply for this position" button
- Similar jobs section
- Social sharing buttons
- Structured data for Google Jobs

**Rendering:** SSG with ISR (revalidate every 1 hour)

**SEO:**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "JobPosting",
  "title": "Senior Software Engineer",
  "description": "...",
  "datePosted": "2026-02-15",
  "employmentType": "FULL_TIME",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "HR-Plus",
    "sameAs": "https://hrplus.com"
  },
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "San Francisco",
      "addressRegion": "CA",
      "addressCountry": "US"
    }
  }
}
</script>
```

### 4. Application Form `/apply/[jobId]`
**Purpose:** Multi-step application submission

**Features:**
- Step 1: Basic Info
  - First name, last name
  - Email, phone
  - Location
  - LinkedIn URL (optional)
  - Portfolio URL (optional)
- Step 2: Resume & Cover Letter
  - Resume upload (PDF, DOCX - max 10MB)
  - Cover letter (rich text editor)
- Step 3: Screening Questions
  - Custom questions defined per job
  - Various input types (text, select, radio, checkbox)
- Step 4: Review & Submit
  - Review all information
  - Terms acceptance
  - Submit button

**Validation:** Client-side with Zod + Server-side in Django

**Success:** Redirect to thank you page with application tracking link

**Rendering:** SSR (protected route - requires login or creates account)

**API:** `POST /api/v1/applications/`

### 5. Candidate Login `/login`
**Purpose:** Authenticate existing candidates

**Features:**
- Email/password form
- "Remember me" checkbox
- "Forgot password?" link
- "Don't have an account? Register" link
- Social login buttons (Phase 2)

**Rendering:** SSR

**API:** `POST /api/v1/auth/login/`

### 6. Candidate Registration `/register`
**Purpose:** Create new candidate account

**Features:**
- First name, last name
- Email (becomes username)
- Password (with strength indicator)
- Terms and privacy policy acceptance
- "Already have an account? Login" link

**Post-registration:** Auto-login and redirect to profile completion

**Rendering:** SSR

**API:** `POST /api/v1/auth/register/`

### 7. Candidate Dashboard `/dashboard`
**Purpose:** Overview of candidate's application journey

**Features:**
- Welcome message with name
- Quick stats:
  - Active applications count
  - Upcoming interviews
  - Offers pending
- Recent activity timeline
- Action items (complete profile, upcoming interview, etc.)
- Quick links (view all applications, edit profile)

**Rendering:** SSR (authenticated route)

**API:** `GET /api/v1/candidates/dashboard/`

### 8. My Applications `/applications`
**Purpose:** List all submitted applications

**Features:**
- Application cards with:
  - Job title
  - Company/department
  - Applied date
  - Current status (Applied, Screening, Interview, Offer, Hired, Rejected)
  - Last updated
  - View details link
- Filter by status
- Search by job title
- Sort options (date applied, status)

**Rendering:** SSR (authenticated)

**API:** `GET /api/v1/applications/?candidate_id=current_user`

### 9. Application Detail `/applications/[id]`
**Purpose:** Detailed view of single application

**Features:**
- Job information
- Application status with visual timeline
- Status history (Applied → Screening → Interview → ...)
- Uploaded documents (resume, cover letter)
- Screening responses
- Interview information (if scheduled)
- Messages/feedback (if any)
- Offer details (if extended)
- Actions (withdraw application, accept/decline offer)

**Rendering:** SSR (authenticated)

**API:** `GET /api/v1/applications/{id}/`

### 10. Candidate Profile `/profile`
**Purpose:** Edit candidate profile and preferences

**Features:**
- Personal information
- Contact details
- Resume management (upload new, view current)
- Work experience (add/edit/delete)
- Education (add/edit/delete)
- Skills
- Job preferences:
  - Desired job types
  - Preferred locations
  - Salary expectations
  - Work authorization
- Privacy settings
- Email notification preferences

**Rendering:** SSR (authenticated)

**API:** `GET/PUT /api/v1/candidates/profile/`

### 11. Upcoming Interviews `/interviews`
**Purpose:** View and manage scheduled interviews

**Features:**
- Interview cards with:
  - Job title
  - Interview type (phone, video, onsite)
  - Date and time
  - Location or video link
  - Interviewers (if available)
  - Preparation notes
- Calendar view option
- Add to personal calendar (iCal export)
- Confirmation/cancellation actions

**Rendering:** SSR (authenticated)

**API:** `GET /api/v1/interviews/?candidate_id=current_user`

### 12. Offers `/offers`
**Purpose:** View and respond to job offers

**Features:**
- Offer cards with:
  - Job title
  - Offer date
  - Expiration date
  - Status (pending, accepted, declined)
  - View details button
- Offer detail page:
  - Position details
  - Compensation package
  - Start date
  - Benefits summary
  - Offer letter (PDF download)
  - Accept/Decline buttons
  - Negotiate button (optional)

**Rendering:** SSR (authenticated)

**API:** `GET /api/v1/offers/?candidate_id=current_user`

---

## Design System

### Color Palette

**Primary:**
- Primary: `#667eea` (Purple - brand color)
- Primary hover: `#5568d3`
- Primary foreground: `#ffffff`

**Secondary:**
- Secondary: `#f3f4f6` (Light gray)
- Secondary foreground: `#1f2937`

**Accent:**
- Accent: `#10b981` (Green - success)
- Warning: `#f59e0b` (Orange)
- Error: `#ef4444` (Red)

**Neutral:**
- Background: `#ffffff`
- Foreground: `#1f2937`
- Muted: `#f3f4f6`
- Border: `#e5e7eb`

### Typography

**Font Family:** Inter (system font stack)

**Headings:**
- H1: 3rem (48px), font-bold
- H2: 2.25rem (36px), font-semibold
- H3: 1.875rem (30px), font-semibold
- H4: 1.5rem (24px), font-medium

**Body:**
- Large: 1.125rem (18px)
- Base: 1rem (16px)
- Small: 0.875rem (14px)

### Components

**Reuse from shared library:**
- Button
- Input
- Select
- Checkbox
- Radio
- Card
- Badge
- Alert
- Dialog
- Dropdown

**Custom components:**
- JobCard
- ApplicationTracker
- InterviewCard
- OfferCard

---

## API Integration

### Endpoints Required

**Jobs:**
- `GET /api/v1/jobs/` - List open jobs
- `GET /api/v1/jobs/{slug}/` - Job detail

**Applications:**
- `POST /api/v1/applications/` - Submit application
- `GET /api/v1/applications/` - List my applications
- `GET /api/v1/applications/{id}/` - Application detail
- `PATCH /api/v1/applications/{id}/` - Withdraw application

**Candidates:**
- `POST /api/v1/auth/register/` - Register candidate
- `POST /api/v1/auth/login/` - Login
- `POST /api/v1/auth/logout/` - Logout
- `GET /api/v1/candidates/profile/` - Get profile
- `PUT /api/v1/candidates/profile/` - Update profile
- `POST /api/v1/candidates/resume/` - Upload resume

**Interviews:**
- `GET /api/v1/interviews/` - My interviews
- `GET /api/v1/interviews/{id}/` - Interview detail

**Offers:**
- `GET /api/v1/offers/` - My offers
- `GET /api/v1/offers/{id}/` - Offer detail
- `POST /api/v1/offers/{id}/accept/` - Accept offer
- `POST /api/v1/offers/{id}/decline/` - Decline offer

---

## SEO Strategy

### Meta Tags
Every public page includes:
```tsx
export const metadata: Metadata = {
  title: 'Page Title | HR-Plus Careers',
  description: 'Compelling description under 160 characters',
  keywords: ['keyword1', 'keyword2', 'keyword3'],
  openGraph: {
    title: 'Page Title',
    description: 'Description',
    images: ['/og-image.jpg'],
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Page Title',
    description: 'Description',
    images: ['/twitter-image.jpg'],
  },
}
```

### Sitemap
- Auto-generated sitemap.xml
- Include all public pages
- Priority and change frequency

### Robots.txt
```
User-agent: *
Allow: /
Disallow: /dashboard/
Disallow: /applications/
Disallow: /profile/
Disallow: /api/

Sitemap: https://careers.hrplus.com/sitemap.xml
```

### Structured Data
- JobPosting schema on job detail pages
- Organization schema on homepage
- BreadcrumbList schema on all pages

---

## Performance Optimization

### Static Site Generation
- Job detail pages: SSG with ISR (1 hour revalidation)
- Homepage: SSG with ISR (5 minutes revalidation)

### Image Optimization
- Use Next.js Image component
- Lazy loading
- WebP format with fallback
- Responsive images with srcset

### Code Splitting
- Dynamic imports for heavy components
- Route-based code splitting (automatic)

### Caching
- Static assets: 1 year cache
- API responses: Appropriate cache headers
- CDN for global distribution

### Performance Targets
- Lighthouse Score: 90+
- First Contentful Paint (FCP): < 1.8s
- Time to Interactive (TTI): < 3.8s
- Cumulative Layout Shift (CLS): < 0.1

---

## Security

### Authentication
- HttpOnly cookies for session
- Secure flag in production
- SameSite=Lax for CSRF protection
- Token expiration after 30 days

### Input Validation
- Client-side with Zod
- Server-side with DRF serializers
- File upload validation (type, size)
- Sanitize user input

### CORS
- Only allow requests from authenticated domain
- Credentials: include for cookies

### Rate Limiting
- Application submission: 5 per hour per IP
- Login attempts: 10 per hour per IP
- API requests: 100 per minute per user

---

## Testing Strategy

### Unit Tests
- Component tests with Jest
- Form validation tests
- Utility function tests

### Integration Tests
- API integration tests
- Authentication flow tests
- Application submission tests

### E2E Tests (Playwright)
- Job search and application flow
- Login and registration flow
- Profile management
- Application tracking

### Performance Tests
- Lighthouse CI
- Load testing with k6

---

## Deployment

### Environment Variables
```bash
# Next.js Public
NEXT_PUBLIC_API_URL=https://api.hrplus.com
NEXT_PUBLIC_SITE_URL=https://careers.hrplus.com

# Next.js Server
DJANGO_API_URL=https://api.hrplus.com
SESSION_SECRET=your-secret-key

# Features
NEXT_PUBLIC_ENABLE_SOCIAL_LOGIN=true
NEXT_PUBLIC_ENABLE_GOOGLE_JOBS=true
```

### Build
```bash
npm run build
npm run start
```

### CDN
- Vercel Edge Network
- Or CloudFlare CDN
- Cache static assets globally

---

## Phase 1 (MVP) - Days 1-7

**Core Features:**
- [ ] Job board with search
- [ ] Job detail pages
- [ ] Application submission
- [ ] Candidate registration/login
- [ ] Basic candidate dashboard
- [ ] My applications page

**Deliverables:**
- Functional career site
- Application submission working
- Basic tracking for candidates

---

## Phase 2 (Enhanced) - Days 8-12

**Additional Features:**
- [ ] Profile management
- [ ] Resume upload integration
- [ ] Interview management
- [ ] Offer management
- [ ] Enhanced dashboard with stats
- [ ] Application timeline view

**Deliverables:**
- Complete candidate portal
- Full application lifecycle

---

## Phase 3 (Polish) - Days 13-15

**Improvements:**
- [ ] SEO optimization
- [ ] Performance tuning
- [ ] Accessibility improvements
- [ ] Social login integration
- [ ] Email notifications integration
- [ ] Analytics integration

**Deliverables:**
- Production-ready site
- SEO optimized
- Analytics tracking

---

## Success Metrics

### User Experience
- Application completion rate > 70%
- Average time to apply < 10 minutes
- Mobile conversion rate > 60%

### Technical
- Page load time < 3 seconds
- Lighthouse score > 90
- Zero critical accessibility issues

### Business
- Application volume increase > 30%
- Candidate satisfaction score > 4/5
- Reduced recruiter time per application

---

## Next Steps

1. **Create Next.js application structure**
2. **Set up routing and layouts**
3. **Implement job board**
4. **Build application form**
5. **Add authentication**
6. **Create candidate dashboard**
7. **Test and optimize**

---

**Status:** Ready to begin implementation
**Priority:** HIGH
**Estimated Completion:** March 3, 2026
