import { http, HttpResponse } from 'msw'
import type { ChatMessage, ChatPart, ChatSession, ChatSessionDetail } from '~/types/api/responses'
import type { ChatMessageVM, ChatPartVM } from '~/services/chat.service'
import { beginTurn, chatStreamReducer, initialChatState } from '~/utils/chatStreamReducer'
import { sseResponse, sseScenarios } from '../sse'
import type { ChatStreamEvent } from '~/types/api/responses'
import { identityFromRequest } from '../token'

const api = '*/api/v1'

interface StoredSession {
  id: string
  userId: number
  organizationId: number
  title: string
  date_created: number
  last_activity_at: number
  messages: ChatMessage[]
}

const memory: { sessions: StoredSession[], nextMessageId: number } = { sessions: [], nextMessageId: 1 }
const STORE_KEY = 'qai:mock-chat'

export function resetChatStore() {
  memory.sessions = []
  memory.nextMessageId = 1
  if (typeof sessionStorage !== 'undefined') sessionStorage.removeItem(STORE_KEY)
}

function readStore(): { sessions: StoredSession[], nextMessageId: number } {
  if (typeof sessionStorage === 'undefined') return memory
  const raw = sessionStorage.getItem(STORE_KEY)
  if (!raw) return { sessions: [], nextMessageId: 1 }
  try {
    return JSON.parse(raw) as { sessions: StoredSession[], nextMessageId: number }
  }
  catch {
    return { sessions: [], nextMessageId: 1 }
  }
}

function writeStore(store: { sessions: StoredSession[], nextMessageId: number }) {
  memory.sessions = store.sessions
  memory.nextMessageId = store.nextMessageId
  if (typeof sessionStorage !== 'undefined') sessionStorage.setItem(STORE_KEY, JSON.stringify(store))
}

function unauthorized() {
  return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
}

function notFound() {
  return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
}

function owned(store: { sessions: StoredSession[] }, identity: { userId: number, organizationId: number }, id: string) {
  return store.sessions.find(session =>
    session.id === id && session.userId === identity.userId && session.organizationId === identity.organizationId,
  )
}

function toSession(session: StoredSession): ChatSession {
  return {
    id: session.id,
    title: session.title,
    date_created: session.date_created,
    last_activity_at: session.last_activity_at,
  }
}

function toPart(part: ChatPartVM): ChatPart {
  if (part.kind === 'text') return { kind: 'text', text: part.text }
  const result = part.result && typeof part.result === 'object'
    ? part.result as Record<string, unknown>
    : null
  return {
    kind: 'tool',
    call_id: part.call_id,
    name: part.name,
    args: part.args,
    result,
    error: part.error ?? null,
    pending_revision_id: part.pending_revision_id ?? null,
    pending_revision_status: part.pending_revision_status ?? null,
  }
}

function toMessage(store: { nextMessageId: number }, message: ChatMessageVM): ChatMessage {
  const dto: ChatMessage = {
    id: store.nextMessageId++,
    role: message.role,
    parts: message.parts.map(toPart),
    model: message.model,
    date_created: Math.floor(message.createdAt.getTime() / 1000),
  }
  return dto
}

function scriptFor(text: string): { events: ChatStreamEvent[], delayMs: number } {
  const normalized = text.trim().toLowerCase().replace(/\s+/g, ' ')
  if (normalized.includes('billing')) return { events: sseScenarios['search-then-answer']!, delayMs: 0 }
  if (normalized.includes('quota')) return { events: sseScenarios.quota!, delayMs: 0 }
  if (normalized.includes('unavailable') || normalized === 'error') return { events: sseScenarios['llm-error']!, delayMs: 0 }
  if (normalized.includes('slow')) return { events: sseScenarios['plain-answer']!, delayMs: 400 }
  return { events: sseScenarios['plain-answer']!, delayMs: 0 }
}

function titleFrom(text: string) {
  const trimmed = text.trim()
  if (trimmed.length <= 60) return trimmed
  const boundary = trimmed.slice(0, 60).lastIndexOf(' ')
  return `${trimmed.slice(0, boundary > 20 ? boundary : 60)}…`
}

export const chatHandlers = [
  http.post(`${api}/chat/sessions`, async ({ request }) => {
    const identity = identityFromRequest(request)
    if (!identity) return unauthorized()
    const body = await request.json().catch(() => ({})) as { title?: string }
    const now = Math.floor(Date.now() / 1000)
    const store = readStore()
    const session: StoredSession = {
      id: crypto.randomUUID(),
      userId: identity.userId,
      organizationId: identity.organizationId,
      title: body.title?.trim() || 'New conversation',
      date_created: now,
      last_activity_at: now,
      messages: [],
    }
    store.sessions.unshift(session)
    writeStore(store)
    return HttpResponse.json(toSession(session), { status: 201 })
  }),

  http.get(`${api}/chat/sessions`, ({ request }) => {
    const identity = identityFromRequest(request)
    if (!identity) return unauthorized()
    const url = new URL(request.url)
    const limit = Number(url.searchParams.get('limit') ?? 20)
    const offset = Number(url.searchParams.get('offset') ?? 0)
    const mine = readStore().sessions.filter(session =>
      session.userId === identity.userId && session.organizationId === identity.organizationId,
    )
    return HttpResponse.json({
      items: mine.slice(offset, offset + limit).map(toSession),
      total: mine.length,
      limit,
      offset,
    })
  }),

  http.get(`${api}/chat/sessions/:id`, ({ request, params }) => {
    const identity = identityFromRequest(request)
    if (!identity) return unauthorized()
    const session = owned(readStore(), identity, String(params.id))
    if (!session) return notFound()
    const detail: ChatSessionDetail = { ...toSession(session), messages: session.messages }
    return HttpResponse.json(detail)
  }),

  http.post(`${api}/chat/sessions/:id/messages`, async ({ request, params }) => {
    const identity = identityFromRequest(request)
    if (!identity) return unauthorized()
    const store = readStore()
    const session = owned(store, identity, String(params.id))
    if (!session) return notFound()
    const body = await request.json().catch(() => ({})) as { text?: string }
    const text = body.text?.trim() ?? ''
    if (!text || text.length > 4000) {
      return HttpResponse.json({ detail: [{ loc: ['body', 'text'], msg: 'text must be 1 to 4000 characters' }] }, { status: 422 })
    }
    const { events, delayMs } = scriptFor(text)
    const script = events.map(event => event.type === 'session' ? { ...event, session_id: session.id } : event)
    let state = beginTurn(initialChatState(session.id), text)
    for (const event of script) state = chatStreamReducer(state, event)
    if (session.title === 'New conversation') session.title = titleFrom(text)
    session.last_activity_at = Math.floor(Date.now() / 1000)
    session.messages = [...session.messages, ...state.messages.map(message => toMessage(store, message))]
    store.sessions.sort((a, b) => b.last_activity_at - a.last_activity_at)
    writeStore(store)
    return sseResponse(script, delayMs)
  }),
]
