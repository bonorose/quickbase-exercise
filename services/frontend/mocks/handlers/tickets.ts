import { http, HttpResponse } from 'msw'
import type { TicketPriority, TicketSort, TicketStatus } from '~/types/api/responses'
import { getTicket, ticketsForOrganization, toTicketSummary } from '../fixtures/tickets'
import { identityFromRequest } from '../token'

const api = '*/api/v1'
const STATUSES: TicketStatus[] = ['open', 'blocked', 'closed']
const PRIORITIES: TicketPriority[] = ['lowest', 'low', 'medium', 'high', 'critical']
const SORTS: TicketSort[] = ['-date_updated', 'date_updated', 'priority', '-priority', 'id']
const PRIORITY_RANK: Record<TicketPriority, number> = {
  lowest: 1,
  low: 2,
  medium: 3,
  high: 4,
  critical: 5,
}

function unauthorized() {
  return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
}

function validation(loc: string[], msg: string) {
  return HttpResponse.json({ detail: [{ loc, msg }] }, { status: 422 })
}

export const ticketHandlers = [
  http.get(`${api}/tickets`, ({ request }) => {
    const identity = identityFromRequest(request)
    if (!identity) return unauthorized()

    const url = new URL(request.url)
    const q = url.searchParams.get('q')?.trim().toLowerCase() ?? ''
    const status = url.searchParams.get('status') ?? undefined
    const priority = url.searchParams.get('priority') ?? undefined
    const sort = (url.searchParams.get('sort') ?? '-date_updated') as TicketSort
    const limit = Number(url.searchParams.get('limit') ?? 20)
    const offset = Number(url.searchParams.get('offset') ?? 0)

    if (status && !STATUSES.includes(status as TicketStatus)) {
      return validation(['query', 'status'], 'Invalid status')
    }
    if (priority && !PRIORITIES.includes(priority as TicketPriority)) {
      return validation(['query', 'priority'], 'Invalid priority')
    }
    if (!SORTS.includes(sort)) {
      return validation(['query', 'sort'], 'Invalid sort')
    }
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
      return validation(['query', 'limit'], 'limit must be between 1 and 100')
    }
    if (!Number.isInteger(offset) || offset < 0) {
      return validation(['query', 'offset'], 'offset must be >= 0')
    }

    let items = ticketsForOrganization(identity.organizationId)
    if (q) items = items.filter(ticket => ticket.title.toLowerCase().includes(q))
    if (status) items = items.filter(ticket => ticket.status === status)
    if (priority) items = items.filter(ticket => ticket.priority === priority)

    items = [...items].sort((a, b) => {
      switch (sort) {
        case 'date_updated':
          return a.date_updated - b.date_updated
        case 'priority':
          return PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority]
        case '-priority':
          return PRIORITY_RANK[b.priority] - PRIORITY_RANK[a.priority]
        case 'id':
          return a.id - b.id
        default:
          return b.date_updated - a.date_updated
      }
    })

    const page = items.slice(offset, offset + limit)
    return HttpResponse.json({
      items: page.map(toTicketSummary),
      total: items.length,
      limit,
      offset,
    })
  }),

  http.get(`${api}/tickets/:id`, ({ request, params }) => {
    const identity = identityFromRequest(request)
    if (!identity) return unauthorized()
    const id = Number(params.id)
    const ticket = getTicket(id, identity.organizationId)
    if (!ticket) {
      return HttpResponse.json({ detail: 'Ticket not found' }, { status: 404 })
    }
    const { organization_id: _organizationId, ...dto } = ticket
    return HttpResponse.json(dto)
  }),

  http.get('*/health', () => HttpResponse.json({ status: 'ok', database: 'up' })),
]
