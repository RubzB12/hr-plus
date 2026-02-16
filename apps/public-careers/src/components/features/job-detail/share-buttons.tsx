'use client'

import { useState } from 'react'

interface ShareButtonsProps {
  job: {
    title: string
    slug: string
    department: string
    location_city?: string
    location_name: string
  }
}

export function ShareButtons({ job }: ShareButtonsProps) {
  const [showCopied, setShowCopied] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)

  // Build the job URL
  const jobUrl = typeof window !== 'undefined'
    ? `${window.location.origin}/jobs/${job.slug}`
    : ''

  // Share text for social media
  const shareText = `Check out this ${job.title} position at ${job.department}${
    job.location_city ? ` in ${job.location_city}` : ''
  }!`

  // Check if Web Share API is available (mobile)
  const canUseNativeShare = typeof navigator !== 'undefined' && navigator.share

  const handleNativeShare = async () => {
    if (!canUseNativeShare) return

    try {
      await navigator.share({
        title: job.title,
        text: shareText,
        url: jobUrl,
      })
      // Track share event (optional)
      console.log('Shared via native share')
    } catch (error) {
      // User cancelled or error occurred
      console.log('Share cancelled or failed')
    }
  }

  const handleLinkedInShare = () => {
    const url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(jobUrl)}`
    window.open(url, '_blank', 'width=600,height=600')
    setShowDropdown(false)
  }

  const handleTwitterShare = () => {
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(jobUrl)}`
    window.open(url, '_blank', 'width=600,height=400')
    setShowDropdown(false)
  }

  const handleFacebookShare = () => {
    const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(jobUrl)}`
    window.open(url, '_blank', 'width=600,height=600')
    setShowDropdown(false)
  }

  const handleEmailShare = () => {
    const subject = encodeURIComponent(`Job Opportunity: ${job.title}`)
    const body = encodeURIComponent(
      `I thought you might be interested in this position:\n\n${job.title}\n${job.department}${
        job.location_city ? `\n${job.location_city}` : ''
      }\n\n${jobUrl}`
    )
    window.location.href = `mailto:?subject=${subject}&body=${body}`
    setShowDropdown(false)
  }

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(jobUrl)
      setShowCopied(true)
      setTimeout(() => setShowCopied(false), 2000)
    } catch (error) {
      // Fallback for older browsers
      const textarea = document.createElement('textarea')
      textarea.value = jobUrl
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setShowCopied(true)
      setTimeout(() => setShowCopied(false), 2000)
    }
    setShowDropdown(false)
  }

  return (
    <div className="relative">
      {/* Mobile: Native Share Button */}
      {canUseNativeShare ? (
        <button
          onClick={handleNativeShare}
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
            />
          </svg>
          Share
        </button>
      ) : (
        /* Desktop: Dropdown with Multiple Options */
        <>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-muted"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
              />
            </svg>
            Share
          </button>

          {/* Dropdown Menu */}
          {showDropdown && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowDropdown(false)}
              />

              {/* Menu */}
              <div className="absolute right-0 top-full z-20 mt-2 w-56 rounded-lg border border-border bg-card shadow-lg">
                <div className="p-2 space-y-1">
                  {/* LinkedIn */}
                  <button
                    onClick={handleLinkedInShare}
                    className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-muted"
                  >
                    <svg className="h-5 w-5 text-[#0A66C2]" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                    Share on LinkedIn
                  </button>

                  {/* Twitter */}
                  <button
                    onClick={handleTwitterShare}
                    className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-muted"
                  >
                    <svg className="h-5 w-5 text-[#1DA1F2]" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                    </svg>
                    Share on Twitter
                  </button>

                  {/* Facebook */}
                  <button
                    onClick={handleFacebookShare}
                    className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-muted"
                  >
                    <svg className="h-5 w-5 text-[#1877F2]" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                    </svg>
                    Share on Facebook
                  </button>

                  <div className="my-1 border-t border-border" />

                  {/* Email */}
                  <button
                    onClick={handleEmailShare}
                    className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-muted"
                  >
                    <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    Share via Email
                  </button>

                  {/* Copy Link */}
                  <button
                    onClick={handleCopyLink}
                    className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-muted"
                  >
                    {showCopied ? (
                      <>
                        <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-green-600">Link copied!</span>
                      </>
                    ) : (
                      <>
                        <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                        </svg>
                        Copy Link
                      </>
                    )}
                  </button>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
