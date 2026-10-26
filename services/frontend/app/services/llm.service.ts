import type { LLMApi } from '~/api/endpoints/llm.api'
import type { LLMStreamEvent } from '~/types/api/responses'

export class LLMService {
  constructor(private readonly api: LLMApi) {}

  /** Yields stream events until `done` or `error`. Throws ApiError if the request itself is rejected (401/422/503). */
  streamCompletion(prompt: string, signal?: AbortSignal): AsyncGenerator<LLMStreamEvent> {
    return this.api.stream({ prompt: prompt.trim() }, signal)
  }
}
