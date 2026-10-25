import type { HealthApi } from '~/api/endpoints/health.api'
import type { ItemsApi } from '~/api/endpoints/items.api'
import type { HealthResponse, ItemResponse } from '~/types/api/responses'
import type { DashboardSummary, ItemSummary, ServiceStatus } from '~/types/models'

function toItemSummary(dto: ItemResponse): ItemSummary {
  return {
    id: dto.id,
    name: dto.name,
    description: dto.description ?? '—',
    createdAt: new Date(dto.created_at),
  }
}

function toStatuses(health: HealthResponse | null): { api: ServiceStatus, database: ServiceStatus } {
  if (!health) return { api: 'down', database: 'down' }
  return { api: health.status === 'ok' ? 'up' : 'degraded', database: health.database }
}

export class DashboardService {
  constructor(
    private readonly itemsApi: ItemsApi,
    private readonly healthApi: HealthApi,
  ) {}

  async getSummary(itemLimit = 10): Promise<DashboardSummary> {
    const [list, health] = await Promise.all([
      this.itemsApi.list({ limit: itemLimit, offset: 0 }),
      // A failing health probe should degrade the dashboard, not break it
      this.healthApi.get().catch(() => null),
    ])
    const statuses = toStatuses(health)
    return {
      totalItems: list.total,
      apiStatus: statuses.api,
      databaseStatus: statuses.database,
      items: list.items.map(toItemSummary),
    }
  }
}
