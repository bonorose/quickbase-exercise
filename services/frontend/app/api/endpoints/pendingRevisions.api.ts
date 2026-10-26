import type { ApiClient } from '~/api/client'
import type {
  ApprovePendingRevisionRequest,
  ClaimPendingRevisionRequest,
  ListPendingRevisionsQuery,
  RejectPendingRevisionRequest,
  SavePendingRevisionRequest,
} from '~/types/api/requests'
import type { ApprovePendingRevisionResponse, PendingRevision } from '~/types/api/responses'

export function createPendingRevisionsApi(client: ApiClient, prefix: string) {
  return {
    list: (query: ListPendingRevisionsQuery = {}) =>
      client.request<PendingRevision[]>(`${prefix}/pending-revisions`, { query }),

    get: (id: string) =>
      client.request<PendingRevision>(`${prefix}/pending-revisions/${id}`),

    claim: (ticketId: number, body: ClaimPendingRevisionRequest) =>
      client.request<PendingRevision>(`${prefix}/tickets/${ticketId}/pending-revisions`, { method: 'POST', body }),

    save: (id: string, body: SavePendingRevisionRequest) =>
      client.request<PendingRevision>(`${prefix}/pending-revisions/${id}`, { method: 'PUT', body }),

    approve: (id: string, body: ApprovePendingRevisionRequest = {}) =>
      client.request<ApprovePendingRevisionResponse>(`${prefix}/pending-revisions/${id}/approve`, { method: 'POST', body }),

    reject: (id: string, body: RejectPendingRevisionRequest = {}) =>
      client.request<PendingRevision>(`${prefix}/pending-revisions/${id}/reject`, { method: 'POST', body }),
  }
}

export type PendingRevisionsApi = ReturnType<typeof createPendingRevisionsApi>
