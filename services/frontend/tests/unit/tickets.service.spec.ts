import { describe, expect, it } from 'vitest'
import { snapshotDiff, toTicketDetail, toTicketRow, unixToDate } from '~/services/tickets.service'
import type { TicketDetailResponse } from '~/types/api/responses'

const detail: TicketDetailResponse = {
  id: 4,
  status: 'open',
  priority: 'high',
  title: 'Billing',
  description: 'AI summary',
  contents: 'Client markdown',
  submitted_by: 'client@example.com',
  date_created: 1_700_000_000,
  updated_by: null,
  date_updated: 1_700_000_100,
  revisions: [{
    id: 'rev-1',
    user: { id: 12, name: 'Pat' },
    initial_contents: { title: 'Billing', contents: 'Client markdown', status: 'open', priority: 'low' },
    changed_contents: { title: 'Billing', contents: 'Client markdown', status: 'blocked', priority: 'high' },
    date_created: 1_700_000_050,
  }],
  discussions: [{ id: 2, user: { id: 12, name: 'Pat' }, contents: 'Note' }],
  open_pending_revision: {
    id: 'draft-1',
    owner: { id: 12, name: 'Pat' },
    origin: 'agent',
    tainted: true,
    status: 'open',
    expires_at: 1_700_000_700,
  },
}

describe('tickets.service', () => {
  it('maps a list row without transforming description', () => {
    const row = toTicketRow({
      id: 4,
      status: 'open',
      priority: 'high',
      title: 'Billing',
      description: 'AI summary',
      date_updated: 1_700_000_100,
    })
    expect(row.description).toBe('AI summary')
    expect(row.updatedAt).toEqual(unixToDate(1_700_000_100))
  })

  it('turns EditableSnapshot pairs into field diffs', () => {
    expect(snapshotDiff(
      { title: 'A', contents: 'x', status: 'open', priority: 'low' },
      { title: 'A', contents: 'x', status: 'blocked', priority: 'high' },
    )).toEqual([
      { field: 'status', from: 'open', to: 'blocked' },
      { field: 'priority', from: 'low', to: 'high' },
    ])
  })

  it('maps a detail payload, newest revisions first, and a missing updater', () => {
    const ticket = toTicketDetail(detail)
    expect(ticket.updatedByName).toBeNull()
    expect(ticket.contents).toBe('Client markdown')
    expect(ticket.revisions[0]?.changes).toEqual([
      { field: 'status', from: 'open', to: 'blocked' },
      { field: 'priority', from: 'low', to: 'high' },
    ])
    expect(ticket.openDraft?.ownerName).toBe('Pat')
  })
})
