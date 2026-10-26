import type { ApiClient } from '~/api/client'
import type { LLMStreamRequest } from '~/types/api/requests'
import type { LLMStreamEvent } from '~/types/api/responses'

export function createLLMApi(client: ApiClient, prefix: string) {
  return {
    stream: (body: LLMStreamRequest, signal?: AbortSignal) =>
      client.stream<LLMStreamEvent>(`${prefix}/llm/stream`, { body, signal }),
  }
}

export type LLMApi = ReturnType<typeof createLLMApi>
