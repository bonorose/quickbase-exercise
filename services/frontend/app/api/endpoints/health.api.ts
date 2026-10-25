import type { ApiClient } from '~/api/client'
import type { HealthResponse } from '~/types/api/responses'

/** /health is served at the API root, outside the versioned prefix */
export function createHealthApi(client: ApiClient) {
  return {
    get: () => client<HealthResponse>('/health'),
  }
}

export type HealthApi = ReturnType<typeof createHealthApi>
