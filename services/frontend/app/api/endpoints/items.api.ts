import type { ApiClient } from '~/api/client'
import type { ListItemsQuery } from '~/types/api/requests'
import type { ItemListResponse, ItemResponse } from '~/types/api/responses'

export function createItemsApi(client: ApiClient, prefix: string) {
  return {
    list: (query: ListItemsQuery = {}) =>
      client<ItemListResponse>(`${prefix}/items`, { query }),

    get: (id: number) =>
      client<ItemResponse>(`${prefix}/items/${id}`),
  }
}

export type ItemsApi = ReturnType<typeof createItemsApi>
