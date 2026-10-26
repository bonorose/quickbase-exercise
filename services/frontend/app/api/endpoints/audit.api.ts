import type { ApiClient } from '~/api/client'
import type { ListAuditQuery } from '~/types/api/requests'
import type { AuditListResponse } from '~/types/api/responses'

export function createAuditApi(client: ApiClient, prefix: string) {
  return {
    list: (query: ListAuditQuery = {}) =>
      client.request<AuditListResponse>(`${prefix}/audit`, { query }),
  }
}

export type AuditApi = ReturnType<typeof createAuditApi>
