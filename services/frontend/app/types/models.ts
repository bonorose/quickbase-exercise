/** View models — what components consume. Built from API DTOs by the services layer. */

import type {
  PendingRevisionOrigin,
  PendingRevisionStatus,
  TicketPriority,
  TicketStatus,
  UserRole,
} from '~/types/api/responses'

export interface Organization {
  id: number
  name: string
}

export interface User {
  id: number
  email: string
  fullName: string
  initials: string
  role: UserRole
  organization: Organization
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthSession {
  token: string
  user: User
}

export interface TicketRow {
  id: number
  status: TicketStatus
  priority: TicketPriority
  title: string
  description: string
  updatedAt: Date
}

export interface FieldChange {
  field: string
  from: string
  to: string
}

export interface RevisionView {
  id: string
  authorName: string
  createdAt: Date
  changes: FieldChange[]
}

export interface DiscussionView {
  id: number
  authorName: string
  contents: string
}

export interface OpenDraftView {
  id: string
  ownerId: number
  ownerName: string
  origin: PendingRevisionOrigin
  tainted: boolean
  status: PendingRevisionStatus
  expiresAt: Date | null
}

export interface TicketDetail {
  id: number
  status: TicketStatus
  priority: TicketPriority
  title: string
  description: string
  contents: string
  submittedBy: string
  createdAt: Date
  updatedByName: string | null
  updatedAt: Date
  revisions: RevisionView[]
  discussions: DiscussionView[]
  openDraft: OpenDraftView | null
}

export type ServiceStatus = 'up' | 'degraded' | 'down'

export interface DashboardSummary {
  openCount: number
  blockedCount: number
  closedCount: number
  apiStatus: ServiceStatus
  databaseStatus: ServiceStatus
  recent: TicketRow[]
}
