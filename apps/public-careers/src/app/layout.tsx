import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import Link from 'next/link'
import Image from 'next/image'
import { cookies } from 'next/headers'
import './globals.css'

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
})

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: {
    default: 'Retailability Careers',
    template: '%s | Retailability Careers',
  },
  description:
    'Discover exciting career opportunities at Retailability. Browse open positions, learn about our culture, and apply to join our team.',
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? 'https://careers.retailability.com'
  ),
  openGraph: {
    type: 'website',
    siteName: 'Retailability Careers',
    title: 'Retailability Careers',
    description:
      'Discover exciting career opportunities at Retailability. Browse open positions and apply to join our team.',
  },
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const cookieStore = await cookies()
  const isLoggedIn = !!cookieStore.get('session')

  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased flex min-h-screen flex-col`}
        suppressHydrationWarning
      >
        <header className="border-b border-border bg-background sticky top-0 z-50">
          <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <Link
              href="/"
              className="text-xl font-bold tracking-tight text-primary"
            >
              HR-Plus
            </Link>
            <div className="flex items-center gap-6">
              <ul className="flex items-center gap-6 text-sm font-medium">
                <li>
                  <Link
                    href="/jobs"
                    className="text-muted-foreground transition-colors hover:text-foreground"
                  >
                    Jobs
                  </Link>
                </li>
                <li>
                  <Link
                    href="/about"
                    className="text-muted-foreground transition-colors hover:text-foreground"
                  >
                    About
                  </Link>
                </li>
              </ul>
              {isLoggedIn ? (
                <div className="flex items-center gap-2 border-l border-border pl-6">
                  <Link
                    href="/dashboard/applications"
                    className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
                  >
                    Dashboard
                  </Link>
                </div>
              ) : (
                <div className="flex items-center gap-2 border-l border-border pl-6">
                  <Link
                    href="/login"
                    className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/register"
                    className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90"
                  >
                    Sign Up
                  </Link>
                </div>
              )}
            </div>
          </nav>
        </header>

        <main className="flex-1">{children}</main>

        <footer className="border-t border-border bg-muted">
          <div className="mx-auto max-w-7xl px-6 py-12">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
              <div>
                <Image
                  src="/retailability_logo.png"
                  alt="Retailability"
                  width={120}
                  height={40}
                />
                <p className="mt-2 text-sm text-muted-foreground">
                  Building the future of hiring. Join our team and make an
                  impact.
                </p>
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">Explore</p>
                <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                  <li>
                    <Link href="/jobs" className="hover:text-foreground">
                      Open Positions
                    </Link>
                  </li>
                  <li>
                    <Link href="/about" className="hover:text-foreground">
                      About Us
                    </Link>
                  </li>
                </ul>
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">Legal</p>
                <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                  <li>
                    <Link href="/privacy" className="hover:text-foreground">
                      Privacy Policy
                    </Link>
                  </li>
                  <li>
                    <Link href="/terms" className="hover:text-foreground">
                      Terms of Service
                    </Link>
                  </li>
                </ul>
              </div>
            </div>
            <div className="mt-10 border-t border-border pt-6 text-center text-xs text-muted-foreground">
              &copy; {new Date().getFullYear()} Retailability. All rights reserved.
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
