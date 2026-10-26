import type { HealthApi } from '~/api/endpoints/health.api'
import type { TicketsApi } from '~/api/endpoints/tickets.api'
import type { HealthResponse } from '~/types/api/responses'
import type { DashboardSummary, ServiceStatus } from '~/types/models'
import { toTicketRow } from '~/services/tickets.service'

function toStatuses(health: HealthResponse | null): { api: ServiceStatus, database: ServiceStatus } {
  if (!health) return { api: 'down', database: 'down' }
  return { api: health.status === 'ok' ? 'up' : 'degraded', database: health.database }
}

export class DashboardService {
  constructor(
    private readonly ticketsApi: TicketsApi,
    private readonly healthApi: HealthApi,
  ) {}

  async getSummary(): Promise<DashboardSummary> {
    const [open, blocked, closed, recent, health] = await Promise.all([
      this.ticketsApi.list({ status: 'open', limit: 1, offset: 0 }),
      this.ticketsApi.list({ status: 'blocked', limit: 1, offset: 0 }),
      this.ticketsApi.list({ status: 'closed', limit: 1, offset: 0 }),
      this.ticketsApi.list({ sort: '-date_updated', limit: 5, offset: 0 }),
      this.healthApi.get().catch(() => null),
    ])
    const statuses = toStatuses(health)
    return {
      openCount: open.total,
      blockedCount: blocked.total,
      closedCount: closed.total,
      apiStatus: statuses.api,
      databaseStatus: statuses.database,
      recent: recent.items.map(toTicketRow),
    }
  }
}
