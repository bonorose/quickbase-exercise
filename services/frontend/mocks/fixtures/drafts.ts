import type { PendingRevision, PendingRevisionAction } from '~/types/api/responses'
import type { ChangedContentsRequest } from '~/types/api/requests'
import type { FixtureUser } from './users'
import { getTicket, ticketRecords } from './tickets'

export interface AuditRow {
  id: number
  organization_id: number
  actor_type: 'user' | 'agent' | 'system'
  actor_id: number | null
  event: string
  session_id: string | null
  ticket_id: number | null
  pending_revision_id: string | null
  payload: Record<string, unknown>
  date_created: number
}

const drafts = new Map<string, PendingRevision & { organization_id: number, user_id: number }>()
const audit: AuditRow[] = []
let auditSeq = 1

function now() {
  return Math.floor(Date.now() / 1000)
}

export function recordAudit(row: Omit<AuditRow, 'id' | 'date_created'>) {
  audit.push({ ...row, id: auditSeq++, date_created: now() })
}

export function auditFor(user: FixtureUser, ticketId?: number, sessionId?: string) {
  return audit.filter((row) => {
    if (row.organization_id !== user.organization.id) return false
    if (user.role !== 'team_lead' && row.actor_id !== user.id) return false
    if (ticketId != null && row.ticket_id !== ticketId) return false
    if (sessionId && row.session_id !== sessionId) return false
    return true
  })
}

function summary(draft: PendingRevision) {
  return {
    id: draft.id,
    owner: draft.owner,
    origin: draft.origin,
    tainted: draft.tainted,
    status: draft.status,
    expires_at: draft.expires_at,
  }
}

function materialize(ticketId: number, organizationId: number) {
  const ticket = getTicket(ticketId, organizationId)
  const open = ticket?.open_pending_revision
  if (!ticket || !open) return null
  const existing = drafts.get(open.id)
  if (existing) return existing
  const draft = {
    id: open.id,
    organization_id: organizationId,
    user_id: open.owner.id,
    ticket: { id: ticket.id, title: ticket.title },
    action: 'update' as const,
    origin: open.origin,
    owner: open.owner,
    session_id: null,
    previous_revision_id: ticket.revisions.at(-1)?.id ?? null,
    changed_contents: { priority: 'high' as const },
    diff: { priority: { from: ticket.priority, to: 'high' as const } },
    tainted: open.tainted,
    status: open.status,
    expires_at: open.expires_at,
    server_time: now(),
    decided_by: null,
    decided_at: null,
    date_created: now(),
    date_updated: now(),
    result: null,
  }
  drafts.set(draft.id, draft)
  return draft
}

export function listDrafts(user: FixtureUser, scope: string) {
  for (const ticket of ticketRecords) {
    if (ticket.organization_id === user.organization.id) materialize(ticket.id, user.organization.id)
  }
  const rows = [...drafts.values()].filter(draft => draft.organization_id === user.organization.id && draft.status === 'open')
  if (scope === 'lead_queue') return rows.filter(draft => draft.tainted)
  return rows.filter(draft => draft.user_id === user.id)
}

export function getDraft(id: string, user: FixtureUser) {
  for (const ticket of ticketRecords) {
    if (ticket.organization_id === user.organization.id) materialize(ticket.id, user.organization.id)
  }
  const draft = drafts.get(id)
  if (!draft || draft.organization_id !== user.organization.id) return null
  if (draft.user_id === user.id) return { ...draft, server_time: now() }
  if (user.role === 'team_lead' && draft.tainted) return { ...draft, server_time: now() }
  return null
}

function applyContents(draft: PendingRevision, changed: ChangedContentsRequest | undefined, action?: PendingRevisionAction) {
  const next = { ...draft.changed_contents, ...changed }
  const diff = { ...draft.diff }
  for (const [field, value] of Object.entries(changed ?? {})) {
    if (value == null) continue
    const previous = diff[field]?.from ?? String(value)
    if (previous !== String(value)) diff[field] = { from: previous, to: String(value) }
  }
  return {
    ...draft,
    action: action ?? draft.action,
    changed_contents: next,
    diff,
    expires_at: null,
    date_updated: now(),
    server_time: now(),
  }
}

export function claimDraft(user: FixtureUser, ticketId: number, action: PendingRevisionAction, changed?: ChangedContentsRequest) {
  const ticket = getTicket(ticketId, user.organization.id)
  if (!ticket) return { error: 'missing' as const }
  const open = materialize(ticket.id, user.organization.id)
  if (open && open.status === 'open') {
    return {
      error: 'conflict' as const,
      body: {
        detail: `being worked on by ${open.owner.name}`,
        pending_revision_id: open.id,
        owner: open.owner,
      },
    }
  }
  const id = `draft-${ticket.id}-${now()}`
  const draft = applyContents({
    id,
    ticket: { id: ticket.id, title: ticket.title },
    action,
    origin: 'human',
    owner: { id: user.id, name: user.name },
    session_id: null,
    previous_revision_id: ticket.revisions.at(-1)?.id ?? null,
    changed_contents: {},
    diff: {},
    tainted: false,
    status: 'open',
    expires_at: null,
    server_time: now(),
    decided_by: null,
    decided_at: null,
    date_created: now(),
    date_updated: now(),
    result: null,
  }, changed, action)
  const stored = { ...draft, organization_id: user.organization.id, user_id: user.id }
  drafts.set(id, stored)
  ticket.open_pending_revision = summary(stored)
  recordAudit({
    organization_id: user.organization.id,
    actor_type: 'user',
    actor_id: user.id,
    event: 'pending_revision_created',
    session_id: null,
    ticket_id: ticket.id,
    pending_revision_id: id,
    payload: { action, origin: 'human', tainted: false },
  })
  return { error: null, draft: stored }
}

export function saveDraft(user: FixtureUser, id: string, changed: ChangedContentsRequest, action?: PendingRevisionAction) {
  const draft = getDraft(id, user)
  if (!draft || draft.status !== 'open') return null
  if (draft.user_id !== user.id) return 'forbidden' as const
  const next = { ...applyContents(draft, changed, action), organization_id: user.organization.id, user_id: draft.user_id }
  drafts.set(id, next)
  recordAudit({
    organization_id: user.organization.id,
    actor_type: 'user',
    actor_id: user.id,
    event: 'pending_revision_saved',
    session_id: draft.session_id,
    ticket_id: draft.ticket.id,
    pending_revision_id: id,
    payload: { action: next.action },
  })
  return next
}

export function decideDraft(user: FixtureUser, id: string, status: 'executed' | 'rejected', changed?: ChangedContentsRequest, action?: PendingRevisionAction) {
  const draft = getDraft(id, user)
  if (!draft || draft.status !== 'open') return null
  if (status === 'executed' && draft.tainted && user.role !== 'team_lead') return 'forbidden' as const
  const ticket = getTicket(draft.ticket.id, user.organization.id)
  const next = {
    ...applyContents(draft, changed, action),
    status,
    decided_by: { id: user.id, name: user.name },
    decided_at: now(),
    result: status === 'executed' ? { revision_id: `rev-${id}` } : {},
    organization_id: user.organization.id,
    user_id: draft.user_id,
  }
  drafts.set(id, next)
  if (ticket) {
    ticket.open_pending_revision = null
    if (status === 'executed' && next.action !== 'delete') {
      if (next.changed_contents.title) ticket.title = next.changed_contents.title
      if (next.changed_contents.contents) ticket.contents = next.changed_contents.contents
      if (next.changed_contents.status) ticket.status = next.changed_contents.status
      if (next.changed_contents.priority) ticket.priority = next.changed_contents.priority
      ticket.date_updated = now()
    }
  }
  recordAudit({
    organization_id: user.organization.id,
    actor_type: 'user',
    actor_id: user.id,
    event: status === 'executed' ? 'pending_revision_approved' : 'pending_revision_rejected',
    session_id: draft.session_id,
    ticket_id: draft.ticket.id,
    pending_revision_id: id,
    payload: { action: next.action },
  })
  if (status === 'executed') {
    recordAudit({
      organization_id: user.organization.id,
      actor_type: 'user',
      actor_id: user.id,
      event: 'ticket_mutated',
      session_id: draft.session_id,
      ticket_id: draft.ticket.id,
      pending_revision_id: id,
      payload: { revision_id: next.result?.revision_id ?? null, action: next.action },
    })
  }
  return next
}
