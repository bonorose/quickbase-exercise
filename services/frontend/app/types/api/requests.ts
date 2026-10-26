/** Request bodies / query params — mirror backend src/schemas/<category>/request.py */

import type { TicketPriority, TicketSort, TicketStatus } from '~/types/api/responses'

export interface LoginRequest {
  email: string
  password: string
}

export interface ListTicketsQuery {
  q?: string
  status?: TicketStatus
  priority?: TicketPriority
  sort?: TicketSort
  limit?: number
  offset?: number
}

export interface CreateChatSessionRequest {
  title?: string
}

export interface SendMessageRequest {
  text: string
}

export interface LLMStreamRequest {
  prompt: string
}

export interface ChangedContentsRequest {
  title?: string
  contents?: string
  status?: TicketStatus
  priority?: TicketPriority
}

export interface ClaimPendingRevisionRequest {
  action: 'update' | 'delete'
  changed_contents?: ChangedContentsRequest
}

export interface SavePendingRevisionRequest {
  changed_contents: ChangedContentsRequest
  action?: 'update' | 'delete'
}

export interface ApprovePendingRevisionRequest {
  changed_contents?: ChangedContentsRequest
  action?: 'update' | 'delete'
}

export interface RejectPendingRevisionRequest {
  reason?: string
}

export interface ListPendingRevisionsQuery {
  status?: 'open' | 'executed' | 'rejected' | 'expired' | 'all'
  ticket_id?: number
  session_id?: string
  scope?: 'mine' | 'lead_queue'
}

export interface ListAuditQuery {
  limit?: number
  offset?: number
  session_id?: string
  ticket_id?: number
}
