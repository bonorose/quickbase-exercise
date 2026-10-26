import type { ApiClient } from '~/api/client'
import type { ListTicketsQuery } from '~/types/api/requests'
import type { TicketDetailResponse, TicketListResponse } from '~/types/api/responses'

export function createTicketsApi(client: ApiClient, prefix: string) {
  return {
    list: (query: ListTicketsQuery = {}) =>
      client.request<TicketListResponse>(`${prefix}/tickets`, { query }),

    get: (id: number) =>
      client.request<TicketDetailResponse>(`${prefix}/tickets/${id}`),
  }
}

export type TicketsApi = ReturnType<typeof createTicketsApi>
