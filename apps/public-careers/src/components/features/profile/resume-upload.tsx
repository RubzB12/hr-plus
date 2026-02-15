'use client'

import { useState, useRef } from 'react'

interface ResumeUploadProps {
  currentResumeUrl?: string | null
  onUploadSuccess?: (data: any) => void
}

export function ResumeUpload({ currentResumeUrl, onUploadSuccess }: ResumeUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleFileUpload = async (file: File) => {
    setError(null)
    setSuccess(null)

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ]
    if (!allowedTypes.includes(file.type)) {
      setError('Please upload a PDF, DOC, DOCX, or TXT file')
      return
    }

    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024
    if (file.size > maxSize) {
      setError('File size must be less than 5MB')
      return
    }

    setIsUploading(true)

    try {
      const formData = new FormData()
      formData.append('resume', file)
      formData.append('auto_populate', 'true')

      const response = await fetch('/api/profile/resume', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Upload failed')
      }

      const data = await response.json()
      setSuccess('Resume uploaded successfully!')
      onUploadSuccess?.(data)

      // Clear input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err: any) {
      setError(err.message || 'Failed to upload resume')
    } finally {
      setIsUploading(false)
    }
  }

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="space-y-4">
      {/* Current Resume */}
      {currentResumeUrl && (
        <div className="flex items-center justify-between rounded-lg border border-border bg-muted/50 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <svg className="h-5 w-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium">Current Resume</p>
              <p className="text-xs text-muted-foreground">Uploaded resume file</p>
            </div>
          </div>
          <a
            href={currentResumeUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download
          </a>
        </div>
      )}

      {/* Upload Area */}
      <div
        className={`relative rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
          isDragging
            ? 'border-primary bg-primary/5'
            : 'border-border bg-muted/30 hover:border-primary/50 hover:bg-muted/50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.doc,.docx,.txt"
          onChange={handleFileSelect}
          className="hidden"
          disabled={isUploading}
        />

        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <svg className="h-8 w-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>

        <h3 className="mt-4 text-lg font-semibold">
          {isUploading ? 'Uploading...' : 'Upload your resume'}
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">
          {isUploading
            ? 'Please wait while we process your file'
            : 'Drag and drop your file here, or click to browse'}
        </p>

        <button
          onClick={handleButtonClick}
          disabled={isUploading}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-primary/90 hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <>
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Uploading...
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Choose File
            </>
          )}
        </button>

        <p className="mt-2 text-xs text-muted-foreground">
          Supported formats: PDF, DOC, DOCX, TXT (Max 5MB)
        </p>
      </div>

      {/* Success Message */}
      {success && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-700">
          <div className="flex items-start gap-3">
            <svg className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{success}</span>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <div className="flex items-start gap-3">
            <svg className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
        </div>
      )}
    </div>
  )
}
