import type { ApiClient } from '~/api/client'
import type { CreateChatSessionRequest, SendMessageRequest } from '~/types/api/requests'
import type { ChatSession, ChatSessionDetail, ChatSessionList, ChatStreamEvent } from '~/types/api/responses'

export interface ListChatSessionsQuery {
  limit?: number
  offset?: number
}

export function createChatApi(client: ApiClient, prefix: string) {
  return {
    createSession: (body: CreateChatSessionRequest = {}) =>
      client.request<ChatSession>(`${prefix}/chat/sessions`, { method: 'POST', body }),

    listSessions: (query: ListChatSessionsQuery = {}) =>
      client.request<ChatSessionList>(`${prefix}/chat/sessions`, { query }),

    getSession: (id: string) =>
      client.request<ChatSessionDetail>(`${prefix}/chat/sessions/${id}`),

    sendMessage: (id: string, body: SendMessageRequest, signal?: AbortSignal) =>
      client.stream<ChatStreamEvent>(`${prefix}/chat/sessions/${id}/messages`, { body, signal }),
  }
}

export type ChatApi = ReturnType<typeof createChatApi>
