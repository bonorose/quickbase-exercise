import { describe, expect, it, vi } from 'vitest'
import { TicketsService } from '~/services/tickets.service'
import type { TicketDetailResponse } from '~/types/api/responses'

describe('TicketsService', () => {
  it('lists rows through the API', async () => {
    const api = {
      list: vi.fn(async () => ({
        items: [{
          id: 1,
          status: 'open' as const,
          priority: 'low' as const,
          title: 'One',
          description: 'd',
          date_updated: 1_700_000_000,
        }],
        total: 1,
        limit: 20,
        offset: 0,
      })),
      get: vi.fn(),
    }
    const service = new TicketsService(api)
    const result = await service.list({ q: 'one' })
    expect(result.total).toBe(1)
    expect(result.rows[0]?.title).toBe('One')
  })

  it('loads a detail record', async () => {
    const detail: TicketDetailResponse = {
      id: 1,
      status: 'open',
      priority: 'low',
      title: 'One',
      description: 'd',
      contents: 'c',
      submitted_by: 'a@b.c',
      date_created: 1_700_000_000,
      updated_by: { id: 1, name: 'Pat' },
      date_updated: 1_700_000_100,
      revisions: [],
      discussions: [],
      open_pending_revision: null,
    }
    const api = { list: vi.fn(), get: vi.fn(async () => detail) }
    const service = new TicketsService(api)
    const ticket = await service.get(1)
    expect(ticket.updatedByName).toBe('Pat')
    expect(ticket.openDraft).toBeNull()
  })
})
