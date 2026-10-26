import type { AuditApi } from '~/api/endpoints/audit.api'
import type { ListAuditQuery } from '~/types/api/requests'
import type { AuditEvent } from '~/types/api/responses'

export interface AuditPage {
  items: AuditEvent[]
  total: number
}

export class AuditService {
  constructor(private readonly api: AuditApi) {}

  async list(query: ListAuditQuery = {}): Promise<AuditPage> {
    const page = await this.api.list(query)
    return { items: page.items, total: page.total }
  }
}
