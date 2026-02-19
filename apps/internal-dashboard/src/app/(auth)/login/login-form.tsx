'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function LoginForm() {
  const [error, setError] = useState<string | null>(null)
  const [isPending, setIsPending] = useState(false)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsPending(true)

    const formData = new FormData(event.currentTarget)

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.get('email'),
          password: formData.get('password'),
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.error ?? 'Invalid email or password.')
        return
      }

      // Cookie is now set — do a full navigation so the server layout
      // reads the fresh cookie and renders the dashboard.
      window.location.href = '/dashboard'
    } catch {
      setError('Unable to connect to the server. Please try again.')
    } finally {
      setIsPending(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}
      <div className="space-y-2">
        <Label htmlFor="email" className="text-slate-700">
          Email
        </Label>
        <Input
          id="email"
          name="email"
          type="email"
          placeholder="you@retailability.com"
          required
          autoComplete="email"
          className="border-slate-200 focus:border-slate-400"
        />
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="password" className="text-slate-700">
            Password
          </Label>
          <Link
            href="/forgot-password"
            className="text-xs text-slate-400 hover:text-slate-600"
          >
            Forgot password?
          </Link>
        </div>
        <Input
          id="password"
          name="password"
          type="password"
          required
          autoComplete="current-password"
          className="border-slate-200 focus:border-slate-400"
        />
      </div>
      <Button
        type="submit"
        className="mt-2 w-full bg-red-600 hover:bg-red-700 text-white"
        disabled={isPending}
      >
        {isPending ? 'Signing in...' : 'Sign in'}
      </Button>
    </form>
  )
}
