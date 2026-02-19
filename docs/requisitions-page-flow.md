# Requisitions Page Flow

> **Internal Dashboard** — How the Requisitions section works, end to end.

---

## Overview

The Requisitions section lets recruiters and HR staff manage job openings (requisitions) from creation through to a filled position. It has three main screens:

1. **Requisitions List** — see all open roles
2. **Requisition Detail** — view and manage a single role
3. **Pipeline Board** — move candidates through hiring stages via a drag-and-drop Kanban board

---

## How Data Flows

```
Django Backend (source of truth)
        │
        ▼
  DAL (lib/dal.ts)         ← server-only file, makes all API calls
        │
        ▼
  Server Component (page.tsx)   ← fetches data server-side, no loading spinners
        │
        ▼
  Client Component              ← handles interactivity (drag, buttons, modals)
        │
        ▼
  Server Action (actions.ts)    ← sends changes back to Django, refreshes cache
```

All data comes from Django. Next.js never touches the database directly.

---

## Screen 1 — Requisitions List (`/requisitions`)

### What it shows
A table of every requisition the logged-in user can access:

| Column | Description |
|---|---|
| Req ID | Unique identifier (e.g. `REQ-0042`) |
| Title | Job title |
| Status | Current state (see status table below) |
| Department | Which department the role belongs to |
| Location | Where the role is based |
| Hiring Manager | Person responsible for the hire |
| Headcount | How many positions filled vs. total (e.g. `1 / 2`) |
| Created | When the requisition was created |

### User actions
- **Click any row** → opens the Requisition Detail page
- **Create Requisition** button → goes to `/requisitions/new` *(form not yet built)*

### Behind the scenes
1. Page loads as a Server Component
2. Calls `getRequisitions()` in the DAL
3. DAL sends `GET /api/v1/internal/requisitions/` with the user's session cookie
4. Django checks permissions and returns the list
5. Page renders the table — no client-side fetching, no loading state needed

---

## Screen 2 — Requisition Detail (`/requisitions/[id]`)

### What it shows
A full breakdown of one requisition, split into sections:

- **Header** — Title, status badge, Req ID, version number
- **Role Info** — Department, location, level, employment type, headcount, salary range (if set)
- **Team** — Hiring manager and recruiter (name + email)
- **Approval Chain** — List of approvers, their decision, and date (if approvals configured)
- **Pipeline Stages** — The stages this requisition uses (e.g. Applied → Screening → Interview → Offer)
- **Job Description** — Full description text
- **Timestamps** — Created, updated, opened, published dates

### Status lifecycle

```
draft → pending_approval → approved → open → filled
                                   ↘ on_hold ↗
                                   ↘ cancelled
```

| Status | Color | Meaning |
|---|---|---|
| `draft` | Gray | Not yet submitted for approval |
| `pending_approval` | Outlined | Waiting on approvers |
| `approved` | Blue | Ready to be published |
| `open` | Blue | Actively accepting applications |
| `on_hold` | Outlined | Paused, not accepting applications |
| `filled` | Gray | All positions filled |
| `cancelled` | Red | Requisition closed without filling |

### Action buttons (appear based on status)

| Status | Available Actions |
|---|---|
| `approved` | **Publish**, Clone |
| `open` | **Put on Hold**, Cancel, Clone |
| `on_hold` | **Reopen**, Cancel, Clone |
| `cancelled` | **Reopen**, Clone |
| `filled` | Clone only |

### What happens when you click an action
1. Client component calls the matching Server Action (e.g. `requisitionPublishAction`)
2. Server Action sends `POST /api/v1/internal/requisitions/{id}/{action}/` to Django
3. Django validates and applies the state change
4. Next.js cache is cleared for the list and detail pages
5. Page refreshes to show the new status

### Navigation from this page
- **View Pipeline** button → goes to the Pipeline Board for this requisition

---

## Screen 3 — Pipeline Board (`/requisitions/[id]/pipeline`)

### What it shows
A Kanban board where each column is a hiring stage. Candidate cards sit inside each column.

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Applied    │  │  Screening   │  │  Interview   │  │    Offer     │
│   (12)       │  │   (6)        │  │   (3)        │  │   (1)        │
├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤
│ Jane Doe     │  │ John Smith   │  │ Alice Brown  │  │ Bob Johnson  │
│ 2 days       │  │ 5 days  🔴   │  │ 1 day        │  │ 3 days       │
│──────────────│  │──────────────│  │──────────────│  │──────────────│
│ Sarah Lee    │  │ ...          │  │ ...          │  │              │
│ 8 days  🔴   │  │              │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

### Candidate card details
Each card shows:
- Candidate name (click to open their Application detail)
- Email address
- Application date
- **Days in current stage** (color-coded as a health indicator)

### Days in stage color coding

| Days | Color | Meaning |
|---|---|---|
| 0–3 days | Gray | Fresh — no action needed |
| 4–7 days | Yellow | Getting stale — check in soon |
| 8+ days | Red + bold | Overdue — candidate may disengage |

### Moving a candidate (drag and drop)
1. Grab a candidate card and drag it to a different stage column
2. The card moves immediately (optimistic update)
3. In the background: `POST /api/v1/internal/applications/{id}/move_to_stage/` is sent to Django
4. **If Django accepts it**: a success toast appears, page data refreshes
5. **If Django rejects it**: the card snaps back to its original stage, an error toast appears

### Compare candidates
1. Click **"Select to Compare"** button to enter selection mode
2. Click up to 4 candidate cards to select them (a checkmark appears)
3. A floating bar appears at the bottom showing how many are selected
4. Click **"Compare"** → navigates to `/compare?ids=id1,id2,...` (comparison page)
5. Click **"Clear"** to deselect all and exit selection mode

### Behind the scenes (data loading)
The page runs two API calls in parallel when loading:
- `getRequisitionDetail(id)` → for the header (title, status)
- `getPipelineBoard(id)` → for all stages and their candidate cards

```
GET /api/v1/internal/requisitions/{id}/
GET /api/v1/internal/requisitions/{id}/pipeline/
```

Both run at the same time using `Promise.all` to keep the page fast.

---

## Authentication & Permissions

- The user's session is stored in an HttpOnly cookie (never visible to JavaScript)
- Every API call from the DAL includes this cookie in the request header
- Django enforces all permissions server-side — Next.js does not duplicate permission logic
- If the session is missing → user is redirected to `/login` by the dashboard layout
- If Django returns 401/403 → the page shows an error state

---

## File Map

| File | What it does |
|---|---|
| [requisitions/page.tsx](../apps/internal-dashboard/src/app/(dashboard)/requisitions/page.tsx) | Requisitions list page (server component) |
| [requisitions/[id]/page.tsx](../apps/internal-dashboard/src/app/(dashboard)/requisitions/[id]/page.tsx) | Requisition detail page (server component) |
| [requisitions/[id]/actions.ts](../apps/internal-dashboard/src/app/(dashboard)/requisitions/[id]/actions.ts) | Server actions: publish, hold, cancel, reopen, clone |
| [requisitions/[id]/requisition-actions.tsx](../apps/internal-dashboard/src/app/(dashboard)/requisitions/[id]/requisition-actions.tsx) | Client component that renders action buttons |
| [requisitions/[id]/pipeline/page.tsx](../apps/internal-dashboard/src/app/(dashboard)/requisitions/[id]/pipeline/page.tsx) | Pipeline Kanban board page (server component) |
| [requisitions/[id]/pipeline/actions.ts](../apps/internal-dashboard/src/app/(dashboard)/requisitions/[id]/pipeline/actions.ts) | Server action: move application to stage |
| [components/features/pipeline/kanban-board.tsx](../apps/internal-dashboard/src/components/features/pipeline/kanban-board.tsx) | Interactive Kanban board (client component, drag & drop) |
| [lib/dal.ts](../apps/internal-dashboard/src/lib/dal.ts) | Data Access Layer — all Django API calls live here |

---

## Known Limitations (Not Yet Built)

| Feature | Status |
|---|---|
| Create Requisition form | Placeholder page only — no form implemented yet |
| Filter/search on list page | DAL supports it, but no UI controls yet |
| Pagination on list page | DAL supports it, but not shown in UI yet |
| Bulk move candidates | Not supported — pipeline only moves one at a time |
