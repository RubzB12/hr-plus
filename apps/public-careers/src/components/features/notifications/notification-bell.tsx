'use client'

import { useEffect, useRef, useState, useTransition } from 'react'
import { useRouter } from 'next/navigation'
import type { CandidateNotification } from '@/types/api'

interface Props {
  initialCount: number
  initialNotifications: CandidateNotification[]
}

function relativeTime(dateString: string) {
  const diff = Date.now() - new Date(dateString).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

const API_URL = process.env.NEXT_PUBLIC_API_URL

export function NotificationBell({ initialCount, initialNotifications }: Props) {
  const [isOpen, setIsOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(initialCount)
  const [notifications, setNotifications] = useState(initialNotifications)
  const [, startTransition] = useTransition()
  const panelRef = useRef<HTMLDivElement>(null)
  const router = useRouter()

  // Close panel on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Poll for unread count every 60 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/notifications/unread-count')
        if (res.ok) {
          const data = await res.json()
          setUnreadCount(data.count ?? 0)
        }
      } catch {
        // Silently fail
      }
    }, 60_000)
    return () => clearInterval(interval)
  }, [])

  const handleMarkRead = async (notification: CandidateNotification) => {
    if (!notification.is_read) {
      try {
        await fetch(`/api/notifications/${notification.id}/mark-read`, { method: 'POST' })
        setNotifications(prev =>
          prev.map(n => n.id === notification.id ? { ...n, is_read: true } : n)
        )
        setUnreadCount(prev => Math.max(0, prev - 1))
      } catch {
        // Silently fail
      }
    }
    setIsOpen(false)
    router.push(notification.link)
  }

  const handleMarkAllRead = async () => {
    try {
      await fetch('/api/notifications/mark-all-read', { method: 'POST' })
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch {
      // Silently fail
    }
  }

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => setIsOpen(v => !v)}
        className="relative flex h-9 w-9 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-5 w-5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-10 z-50 w-80 rounded-xl border border-gray-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
            <span className="text-sm font-semibold text-gray-900">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-blue-600 hover:text-blue-700"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-gray-500">
                No notifications yet
              </div>
            ) : (
              notifications.slice(0, 10).map(notification => (
                <button
                  key={notification.id}
                  onClick={() => handleMarkRead(notification)}
                  className={`w-full border-b border-gray-50 px-4 py-3 text-left transition-colors last:border-0 hover:bg-gray-50 ${
                    !notification.is_read ? 'bg-blue-50/50' : ''
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {!notification.is_read && (
                      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-blue-500" />
                    )}
                    <div className={!notification.is_read ? '' : 'ml-4'}>
                      <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                      <p className="mt-0.5 text-xs text-gray-500 line-clamp-2">{notification.body}</p>
                      <p className="mt-1 text-xs text-gray-400">{relativeTime(notification.created_at)}</p>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
