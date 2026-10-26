import { http, HttpResponse } from 'msw'
import { auditFor } from '../fixtures/drafts'
import { findUserById } from '../fixtures/users'
import { identityFromRequest } from '../token'

const api = '*/api/v1'

export const auditHandlers = [
  http.get(`${api}/audit`, ({ request }) => {
    const identity = identityFromRequest(request)
    const user = identity ? findUserById(identity.userId) : undefined
    if (!user) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const url = new URL(request.url)
    const ticket = url.searchParams.get('ticket_id')
    const ticketId = ticket ? Number(ticket) : undefined
    const sessionId = url.searchParams.get('session_id') ?? undefined
    const items = auditFor(user, Number.isInteger(ticketId) ? ticketId : undefined, sessionId).map(row => ({
      id: row.id,
      actor_type: row.actor_type,
      actor: row.actor_id == null ? null : { id: row.actor_id, name: findUserById(row.actor_id)?.name ?? 'Someone' },
      event: row.event,
      session_id: row.session_id,
      ticket_id: row.ticket_id,
      pending_revision_id: row.pending_revision_id,
      payload: row.payload,
      date_created: row.date_created,
    }))
    return HttpResponse.json({ items, total: items.length })
  }),
]
