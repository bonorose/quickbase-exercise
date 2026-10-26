import type { Component } from 'vue'
import { ClipboardList, LayoutDashboard, MessageSquare, ScrollText, Shield, Ticket } from 'lucide-vue-next'

export interface NavItem {
  to: string
  label: string
  icon: Component
  enabled: boolean
}

export function isNavItemActive(path: string, to: string) {
  return to === '/' ? path === '/' : path === to || path.startsWith(`${to}/`)
}

export const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, enabled: true },
  { to: '/tickets', label: 'Tickets', icon: Ticket, enabled: true },
  { to: '/drafts', label: 'Drafts', icon: ClipboardList, enabled: true },
  { to: '/review', label: 'Review', icon: Shield, enabled: true },
  { to: '/chat', label: 'Chat', icon: MessageSquare, enabled: true },
  { to: '/audit', label: 'Audit', icon: ScrollText, enabled: true },
]

export function navItemsFor(role: string | null) {
  return navItems.filter(item => item.enabled && (item.to !== '/review' || role === 'team_lead'))
}
