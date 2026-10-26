import type { ChatApi } from '~/api/endpoints/chat.api'
import type { ListChatSessionsQuery } from '~/api/endpoints/chat.api'
import type {
  ChatMessage,
  ChatPart,
  ChatSession,
  ChatSessionDetail,
  ChatStreamErrorCode,
  ChatStreamEvent,
  PendingRevision,
} from '~/types/api/responses'

export interface ChatSessionVM {
  id: string
  title: string
  createdAt: Date
  lastActivityAt: Date
}

export interface ChatToolPartVM {
  kind: 'tool'
  call_id: string
  name: string
  args: Record<string, unknown>
  ok?: boolean
  result?: unknown
  error?: string
  pending_revision_id?: string | null
  pending_revision_status?: string | null
}

export type ChatTextPartVM = { kind: 'text', text: string }
export type ChatPartVM = ChatTextPartVM | ChatToolPartVM

export interface ChatMessageVM {
  id: string
  role: 'user' | 'assistant' | 'system'
  parts: ChatPartVM[]
  model: string | null
  createdAt: Date
  stopped?: boolean
  error?: { message: string, code?: ChatStreamErrorCode } | null
}

export interface ChatSessionDetailVM extends ChatSessionVM {
  messages: ChatMessageVM[]
  pendingApproval: PendingRevision | null
}

function unixToDate(seconds: number): Date {
  return new Date(seconds * 1000)
}

export function toChatSession(dto: ChatSession): ChatSessionVM {
  return {
    id: dto.id,
    title: dto.title || 'New conversation',
    createdAt: unixToDate(dto.date_created),
    lastActivityAt: unixToDate(dto.last_activity_at),
  }
}

function toPart(part: ChatPart): ChatPartVM {
  if (part.kind === 'text') return { kind: 'text', text: part.text }
  const error = part.error ?? undefined
  return {
    kind: 'tool',
    call_id: part.call_id,
    name: part.name,
    args: part.args,
    ok: error ? false : part.result != null ? true : undefined,
    result: part.result ?? undefined,
    error,
    pending_revision_id: part.pending_revision_id,
    pending_revision_status: part.pending_revision_status,
  }
}

export function toChatMessage(dto: ChatMessage): ChatMessageVM {
  return {
    id: String(dto.id),
    role: dto.role,
    parts: dto.parts.map(toPart),
    model: dto.model,
    createdAt: unixToDate(dto.date_created),
  }
}

/** A stored tool part that already names a pending revision stands in until M3 loads the full record. */
export function pendingFromMessages(messages: ChatMessageVM[]): PendingRevision | null {
  for (const message of messages) {
    for (const part of message.parts) {
      if (part.kind !== 'tool' || !part.pending_revision_id) continue
      const status = part.pending_revision_status
      if (status == null || status === 'open') {
        return { id: part.pending_revision_id } as PendingRevision
      }
    }
  }
  return null
}

export function toChatSessionDetail(dto: ChatSessionDetail): ChatSessionDetailVM {
  const messages = dto.messages.map(toChatMessage)
  return {
    ...toChatSession(dto),
    messages,
    pendingApproval: pendingFromMessages(messages),
  }
}

export class ChatService {
  constructor(private readonly api: ChatApi) {}

  async createSession(title?: string): Promise<ChatSessionVM> {
    return toChatSession(await this.api.createSession(title ? { title } : {}))
  }

  async listSessions(query: ListChatSessionsQuery = {}): Promise<{ items: ChatSessionVM[], total: number, limit: number, offset: number }> {
    const page = await this.api.listSessions(query)
    return {
      items: page.items.map(toChatSession),
      total: page.total,
      limit: page.limit,
      offset: page.offset,
    }
  }

  async getSession(id: string): Promise<ChatSessionDetailVM> {
    return toChatSessionDetail(await this.api.getSession(id))
  }

  sendMessage(id: string, text: string, signal?: AbortSignal): AsyncGenerator<ChatStreamEvent> {
    return this.api.sendMessage(id, { text }, signal)
  }
}
