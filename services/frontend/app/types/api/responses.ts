/** Response bodies — mirror backend src/schemas/<category>/response.py (ROADMAP v1.2) */

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export type UserRole = 'operator' | 'team_lead'

export interface OrganizationSummary {
  id: number
  name: string
}

export interface UserResponse {
  id: number
  name: string
  email: string
  role: UserRole
  organization: OrganizationSummary
}

export interface ActorRef {
  id: number
  name: string
}

export type TicketStatus = 'open' | 'blocked' | 'closed'
export type TicketPriority = 'lowest' | 'low' | 'medium' | 'high' | 'critical'
export type TicketSort = '-date_updated' | 'date_updated' | 'priority' | '-priority' | 'id'

export interface TicketSummary {
  id: number
  status: TicketStatus
  priority: TicketPriority
  title: string
  description: string
  date_updated: number
}

export interface TicketListResponse {
  items: TicketSummary[]
  total: number
  limit: number
  offset: number
}

export interface EditableSnapshot {
  title: string
  contents: string
  status: TicketStatus
  priority: TicketPriority
}

export interface Ticket {
  id: number
  status: TicketStatus
  priority: TicketPriority
  title: string
  description: string
  contents: string
  submitted_by: string
  date_created: number
  updated_by: ActorRef | null
  date_updated: number
}

export interface Revision {
  id: string
  user: ActorRef
  initial_contents: EditableSnapshot
  changed_contents: EditableSnapshot
  date_created: number
}

export interface Discussion {
  id: number
  user: ActorRef
  contents: string
}

export type PendingRevisionAction = 'update' | 'delete'
export type PendingRevisionOrigin = 'human' | 'agent'
export type PendingRevisionStatus = 'open' | 'executed' | 'rejected' | 'expired'

export interface PendingRevisionSummary {
  id: string
  owner: ActorRef
  origin: PendingRevisionOrigin
  tainted: boolean
  status: PendingRevisionStatus
  expires_at: number | null
}

export interface PendingRevision {
  id: string
  ticket: { id: number, title: string }
  action: PendingRevisionAction
  origin: PendingRevisionOrigin
  owner: ActorRef
  session_id: string | null
  previous_revision_id: string | null
  changed_contents: Partial<EditableSnapshot>
  diff: Record<string, { from: string, to: string }>
  tainted: boolean
  status: PendingRevisionStatus
  expires_at: number | null
  server_time: number
  decided_by: ActorRef | null
  decided_at: number | null
  date_created: number
  date_updated: number
  result: Record<string, unknown> | null
}

export interface TicketDetailResponse extends Ticket {
  revisions: Revision[]
  discussions: Discussion[]
  open_pending_revision: PendingRevisionSummary | null
}

export interface HealthResponse {
  status: 'ok' | 'degraded'
  database: 'up' | 'down'
}

/** FastAPI returns a string for domain errors and a list for request validation errors */
export interface ErrorResponse {
  detail: string | { msg: string, loc: (string | number)[] }[]
  pending_revision_id?: string
  owner?: ActorRef
}

/** SSE events from POST /llm/stream — mirror backend schemas/llm/response.py.
 *  Order: status* -> delta* -> exactly one of done | error. */
export type LLMStreamEvent =
  | { type: 'status', message: string }
  | { type: 'delta', text: string }
  | { type: 'done', model: string, text: string }
  | { type: 'error', message: string }

export interface ChatSession {
  id: string
  title: string
  date_created: number
  last_activity_at: number
}

export interface ChatSessionList {
  items: ChatSession[]
  total: number
  limit: number
  offset: number
}

export interface ChatTextPart {
  kind: 'text'
  text: string
}

export interface ChatToolPart {
  kind: 'tool'
  call_id: string
  name: string
  args: Record<string, unknown>
  result?: Record<string, unknown> | null
  error?: string | null
  pending_revision_id?: string | null
  pending_revision_status?: string | null
}

export type ChatPart = ChatTextPart | ChatToolPart

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  parts: ChatPart[]
  model: string | null
  date_created: number
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[]
}

export type ChatStreamErrorCode = 'llm_unavailable' | 'quota_exhausted' | 'internal'

/** C-20 chat stream events (v1.2). Grammar:
 *  session → (status | delta | tool_call | tool_result | approval_required)* → (done | error) */
export type ChatStreamEvent =
  | { type: 'session', session_id: string }
  | { type: 'status', message: string }
  | { type: 'delta', text: string }
  | { type: 'tool_call', call_id: string, name: string, args: Record<string, unknown> }
  | { type: 'tool_result', call_id: string, ok: boolean, result?: unknown, error?: string }
  | { type: 'approval_required', call_id: string, pending_revision: PendingRevision }
  | { type: 'done', message_id: string, model: string }
  | { type: 'error', message: string, code?: ChatStreamErrorCode }

export interface AuditEvent {
  id: number
  actor_type: 'user' | 'agent' | 'system'
  actor: ActorRef | null
  event: string
  session_id: string | null
  ticket_id: number | null
  pending_revision_id: string | null
  payload: Record<string, unknown>
  date_created: number
}

export interface AuditListResponse {
  items: AuditEvent[]
  total: number
}

export interface ApprovePendingRevisionResponse {
  pending_revision: PendingRevision
  ticket: TicketDetailResponse
}
