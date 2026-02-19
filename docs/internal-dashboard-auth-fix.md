# Internal Dashboard Auth Fix

**Date:** 2026-02-18
**Symptom:** Applications submitted on the public careers site did not appear in the internal dashboard. Login to the internal dashboard redirected back to the login page.

---

## Root Causes

### 1. Wrong cookie name in middleware (primary blocker)

**File:** `apps/internal-dashboard/src/middleware.ts`

The middleware checked for the public candidate site's `session` cookie instead of `internal_session`. Since middleware runs before any page or layout, every request to a protected route was immediately redirected back to `/login` regardless of whether the user was logged in.

```diff
- const session = request.cookies.get('session')
+ const session = request.cookies.get('internal_session')
```

---

### 2. Wrong cookie name in dashboard layout

**File:** `apps/internal-dashboard/src/app/(dashboard)/layout.tsx`

Same mismatch as the middleware. If the user had the public site's `session` cookie (e.g., from being logged in as a candidate on `localhost:3000`), the layout would pass the auth check — but then every DAL call would fail because `internal_session` was never found.

```diff
- const session = cookieStore.get('session')
+ const session = cookieStore.get('internal_session')
```

---

### 3. Login action could not set the cookie reliably

**File:** `apps/internal-dashboard/src/app/(auth)/login/actions.ts`

The original login action tried to parse the `sessionid` value out of Django's `Set-Cookie` response header. Server-to-server `fetch` calls (Next.js → Django) do not reliably forward the `Set-Cookie` header. Django already returns the session key explicitly as `data.token` in the JSON response body — exactly how the public site login works — so the action was changed to read that instead.

Additionally, `cookies().set()` and `redirect()` were both inside a `try/catch`. When `redirect()` throws internally and is re-thrown from a `catch` block, Next.js does not reliably flush pending cookie mutations into the redirect response. The fix moves the cookie-set and redirect outside the `try/catch`.

```diff
- // Parse sessionid out of Set-Cookie header (unreliable server-to-server)
- const setCookieHeader = response.headers.get('set-cookie')
- const sessionMatch = setCookieHeader.match(/sessionid=([^;]+)/)
- if (sessionMatch) { cookieStore.set('internal_session', sessionMatch[1], ...) }
- redirect('/dashboard')   // ← inside try/catch

+ // Read token from JSON body (same pattern as public site)
+ token = data.token
  ...
+ // Outside try/catch so cookie is flushed before redirect
+ cookieStore.set('internal_session', token, { ... })
+ redirect('/dashboard')
```

---

### 4. Login form used `useActionState` + Server Action redirect (cookie dropped)

**Files:**
- `apps/internal-dashboard/src/app/(auth)/login/login-form.tsx`
- `apps/internal-dashboard/src/app/api/auth/login/route.ts` *(new)*

When a Server Action is invoked via React's `useActionState`, Next.js routes the response through RSC streaming rather than issuing a plain HTTP redirect. Cookie mutations set before `redirect()` can be dropped in this flow.

The fix replaces the Server Action form with a client-side `fetch` call to a new Route Handler. Route Handlers issue standard HTTP responses, so `Set-Cookie` headers are reliably delivered to the browser.

**New Route Handler** (`app/api/auth/login/route.ts`):
- Calls Django login endpoint
- Validates `data.is_internal`
- Sets `internal_session` cookie via `NextResponse.cookies.set()`
- Returns `{ success: true }`

**Updated login form** (`login-form.tsx`):
- Uses `fetch('/api/auth/login', ...)` instead of `useActionState`
- On success: `window.location.href = '/dashboard'` (full navigation ensures the fresh cookie is sent with the next request)
- On error: displays the error message inline

---

## Why applications weren't visible in the internal dashboard

Once the auth bugs above were present, the internal dashboard's Applications page (`/applications`) was protected by the middleware redirect loop. If a user somehow bypassed this (e.g., via the public site's `session` cookie), the DAL's `getAuthHeaders()` function would throw `'Unauthorized - No session cookie found'` when looking for `internal_session`. The page silently caught this error and displayed "No applications found." rather than an error message.

A secondary fix was applied to the Applications page to surface the error rather than swallow it:

**File:** `apps/internal-dashboard/src/app/(dashboard)/applications/page.tsx`

```diff
- } catch {
-   // API not available yet — show empty state
- }

+ } catch (err) {
+   fetchError = err instanceof Error ? err.message : 'Failed to load applications'
+ }
  ...
+ {fetchError && (
+   <div className="... text-destructive">
+     Failed to load applications: {fetchError}
+   </div>
+ )}
```

---

## Files Changed

| File | Change |
|------|--------|
| `apps/internal-dashboard/src/middleware.ts` | Cookie name: `session` → `internal_session` |
| `apps/internal-dashboard/src/app/(dashboard)/layout.tsx` | Cookie name: `session` → `internal_session` |
| `apps/internal-dashboard/src/app/(auth)/login/actions.ts` | Read `data.token` from JSON body; move cookie-set + redirect outside `try/catch` |
| `apps/internal-dashboard/src/app/(auth)/login/login-form.tsx` | Replace `useActionState` with client-side `fetch` to Route Handler |
| `apps/internal-dashboard/src/app/api/auth/login/route.ts` | New Route Handler for login (sets cookie via `NextResponse`) |
| `apps/internal-dashboard/src/app/(dashboard)/applications/page.tsx` | Expose API errors instead of silently showing empty state |
