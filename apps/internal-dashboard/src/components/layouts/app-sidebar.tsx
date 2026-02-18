'use client'

import Link from 'next/link'
import Image from 'next/image'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  FileText,
  Users,
  UserSearch,
  Calendar,
  DollarSign,
  BarChart3,
  Settings,
  Briefcase,
  MapPin,
  Building2,
  GitBranch,
} from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from '@/components/ui/sidebar'

const overviewItems = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { title: 'Analytics', href: '/analytics', icon: BarChart3 },
]

const hiringItems = [
  { title: 'Pipeline', href: '/pipeline', icon: GitBranch },
  { title: 'Requisitions', href: '/requisitions', icon: FileText },
  { title: 'Applications', href: '/applications', icon: Briefcase },
  { title: 'Candidates', href: '/candidates', icon: UserSearch },
]

const interviewOfferItems = [
  { title: 'Interviews', href: '/interviews', icon: Calendar },
  { title: 'Offers', href: '/offers', icon: DollarSign },
]

const settingsItems = [
  { title: 'Departments', href: '/settings/departments', icon: Building2 },
  { title: 'Locations', href: '/settings/locations', icon: MapPin },
  { title: 'Users', href: '/settings/users', icon: Users },
  { title: 'General Settings', href: '/settings', icon: Settings },
]

export function AppSidebar() {
  const pathname = usePathname()

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === href
    }
    return pathname.startsWith(href)
  }

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-6 py-4">
        <Link href="/dashboard">
          <Image
            src="/retailability_logo.png"
            alt="Retailability"
            width={140}
            height={48}
            priority
          />
        </Link>
      </SidebarHeader>

      <SidebarContent>
        {/* Overview Section */}
        <SidebarGroup>
          <SidebarGroupLabel>Overview</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {overviewItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton asChild isActive={isActive(item.href)}>
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Hiring Section */}
        <SidebarGroup>
          <SidebarGroupLabel>Hiring</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {hiringItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton asChild isActive={isActive(item.href)}>
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Interviews & Offers Section */}
        <SidebarGroup>
          <SidebarGroupLabel>Interviews & Offers</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {interviewOfferItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton asChild isActive={isActive(item.href)}>
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Administration Section */}
        <SidebarGroup>
          <SidebarGroupLabel>Administration</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {settingsItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton asChild isActive={isActive(item.href)}>
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t p-4">
        <div className="text-xs text-muted-foreground text-center">
          <p className="font-semibold">Retailability HR</p>
          <p>v1.0.0</p>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
