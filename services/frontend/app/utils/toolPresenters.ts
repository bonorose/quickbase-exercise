export interface TicketRef {
  id: number
  title: string
}

const TITLES: Record<string, string> = {
  search_tickets: 'Searched tickets',
  mutate_ticket: 'Proposed change',
}

export function toolTitle(name: string): string {
  return TITLES[name] ?? name
}

const STATUS_LABELS: Record<string, string> = {
  open: 'Awaiting approval',
  executed: 'Approved',
  rejected: 'Rejected',
  expired: 'Expired',
}

export function toolStateLabel(part: {
  ok?: boolean
  error?: string
  pending_revision_id?: string | null
  pending_revision_status?: string | null
}): string {
  const status = part.pending_revision_status
  if (status && STATUS_LABELS[status]) return STATUS_LABELS[status]
  if (part.pending_revision_id && part.ok !== false) return 'Awaiting approval'
  if (part.ok === true) return 'Done'
  if (part.ok === false) return 'Failed'
  return 'Running…'
}

/** T-01 results use `tickets`. Older fixtures used `items`. */
export function ticketRefs(result: unknown): TicketRef[] {
  if (!result || typeof result !== 'object') return []
  const record = result as { tickets?: unknown, items?: unknown }
  const rows = Array.isArray(record.tickets) ? record.tickets : Array.isArray(record.items) ? record.items : []
  return rows.flatMap((row) => {
    if (!row || typeof row !== 'object') return []
    const ticket = row as { id?: unknown, title?: unknown }
    const id = Number(ticket.id)
    if (!Number.isInteger(id) || id < 1) return []
    return [{ id, title: typeof ticket.title === 'string' ? ticket.title : `Ticket ${id}` }]
  })
}

/** Read tools can't change anything; worth saying next to the name. */
export function isReadOnlyTool(name: string): boolean {
  return name === 'search_tickets'
}

/** The ticket a mutate call targets, from its arguments. */
export function targetTicketId(part: { name: string, args: Record<string, unknown> }): number | null {
  if (part.name !== 'mutate_ticket') return null
  const id = Number(part.args.id)
  return Number.isInteger(id) && id > 0 ? id : null
}

/** One line for a trace row: what was asked and, once known, what came back. */
export function toolSummary(part: {
  name: string
  args: Record<string, unknown>
  ok?: boolean
  result?: unknown
}): string {
  if (part.name === 'search_tickets') {
    const query = typeof part.args.query === 'string' ? part.args.query : ''
    const asked = query ? `Searched tickets for "${query}"` : 'Searched tickets'
    if (part.ok !== true) return asked
    const found = ticketRefs(part.result).length
    return `${asked} · ${found} found`
  }
  if (part.name === 'mutate_ticket') {
    const id = targetTicketId(part)
    const action = part.args.action === 'delete' ? 'Proposed deleting' : 'Proposed change to'
    return id ? `${action} ticket #${id}` : 'Proposed change'
  }
  return toolTitle(part.name)
}

/** Visual tone for a trace state. `attention` means a person has to act. */
export function toolTone(part: {
  ok?: boolean
  pending_revision_id?: string | null
  pending_revision_status?: string | null
}): 'running' | 'done' | 'attention' | 'failed' | 'closed' {
  const status = part.pending_revision_status
  if (status === 'open' || (part.pending_revision_id && !status && part.ok !== false)) return 'attention'
  if (status === 'rejected' || status === 'expired') return 'closed'
  if (status === 'executed' || part.ok === true) return 'done'
  if (part.ok === false) return 'failed'
  return 'running'
}

export function resultText(result: unknown): string {
  if (result == null) return ''
  if (typeof result === 'string') return result
  return JSON.stringify(result, null, 2)
}
