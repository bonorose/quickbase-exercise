import { describe, expect, it, vi } from 'vitest'
import { DashboardService } from '~/services/dashboard.service'

describe('DashboardService', () => {
  it('counts each status from C-03 totals and maps recent rows', async () => {
    const ticketsApi = {
      list: vi.fn(async (query: { status?: string, limit?: number }) => {
        if (query.status === 'open') return { items: [], total: 7, limit: 1, offset: 0 }
        if (query.status === 'blocked') return { items: [], total: 2, limit: 1, offset: 0 }
        if (query.status === 'closed') return { items: [], total: 4, limit: 1, offset: 0 }
        return {
          items: [{ id: 1, status: 'open', priority: 'high', title: 'One', description: 'd', date_updated: 1_700_000_000 }],
          total: 13,
          limit: 5,
          offset: 0,
        }
      }),
      get: vi.fn(),
    }
    const healthApi = { get: vi.fn(async () => ({ status: 'ok' as const, database: 'up' as const })) }
    const service = new DashboardService(ticketsApi, healthApi)
    const summary = await service.getSummary()
    expect(summary.openCount).toBe(7)
    expect(summary.blockedCount).toBe(2)
    expect(summary.closedCount).toBe(4)
    expect(summary.recent[0]?.title).toBe('One')
    expect(summary.apiStatus).toBe('up')
    expect(ticketsApi.list).toHaveBeenCalledTimes(4)
  })
})
