import type { ChatMessageVM, ChatPartVM, ChatToolPartVM } from '~/services/chat.service'
import type { ChatStreamErrorCode, ChatStreamEvent, PendingRevision } from '~/types/api/responses'

export interface ChatStreamState {
  sessionId: string | null
  messages: ChatMessageVM[]
  status: string | null
  streaming: boolean
  pendingApproval: PendingRevision | null
  lastError: { message: string, code?: ChatStreamErrorCode } | null
  model: string | null
  terminal: boolean
}

export function initialChatState(sessionId: string | null = null): ChatStreamState {
  return {
    sessionId,
    messages: [],
    status: null,
    streaming: false,
    pendingApproval: null,
    lastError: null,
    model: null,
    terminal: false,
  }
}

export function beginTurn(state: ChatStreamState, text: string): ChatStreamState {
  return {
    ...state,
    streaming: true,
    terminal: false,
    status: null,
    lastError: null,
    model: null,
    messages: [
      ...state.messages,
      {
        id: `local-user-${state.messages.length}`,
        role: 'user',
        parts: [{ kind: 'text', text }],
        model: null,
        createdAt: new Date(),
      },
    ],
  }
}

export function markStopped(state: ChatStreamState): ChatStreamState {
  const messages = state.messages.map(message => ({ ...message, parts: message.parts.map(part => ({ ...part })) }))
  const last = messages.at(-1)
  if (!last || last.role !== 'assistant') {
    messages.push({
      id: 'local-stopped',
      role: 'assistant',
      parts: [],
      model: state.model,
      createdAt: new Date(),
      stopped: true,
    })
  }
  else {
    messages[messages.length - 1] = { ...last, stopped: true }
  }
  return { ...state, messages, streaming: false, status: null, terminal: true }
}

function assistant(state: ChatStreamState): { messages: ChatMessageVM[], index: number } {
  const messages = state.messages.map(message => ({ ...message, parts: [...message.parts] }))
  const last = messages.at(-1)
  if (last?.role === 'assistant') return { messages, index: messages.length - 1 }
  messages.push({
    id: 'local-assistant',
    role: 'assistant',
    parts: [],
    model: null,
    createdAt: new Date(),
  })
  return { messages, index: messages.length - 1 }
}

function withAssistant(state: ChatStreamState, update: (message: ChatMessageVM) => ChatMessageVM): ChatStreamState {
  const { messages, index } = assistant(state)
  messages[index] = update(messages[index]!)
  return { ...state, messages, status: null }
}

function devWarn(message: string, detail?: unknown) {
  if (import.meta.dev || import.meta.env.DEV) console.warn(message, detail)
}

function clearStatus(state: ChatStreamState): ChatStreamState {
  return state.status == null ? state : { ...state, status: null }
}

/**
 * Fold one C-20 event into chat state.
 * Events after `done` or `error` are ignored. `approval_required` is recorded and does not end the turn.
 */
export function chatStreamReducer(state: ChatStreamState, event: ChatStreamEvent): ChatStreamState {
  if (state.terminal) {
    devWarn('Ignoring chat event after a terminal event', event.type)
    return state
  }

  switch (event.type) {
    case 'session':
      return { ...clearStatus(state), sessionId: event.session_id }
    case 'status':
      return { ...state, status: event.message }
    case 'delta':
      return withAssistant(state, (message) => {
        const parts = [...message.parts]
        const tail = parts.at(-1)
        if (tail?.kind === 'text') parts[parts.length - 1] = { kind: 'text', text: tail.text + event.text }
        else parts.push({ kind: 'text', text: event.text })
        return { ...message, parts }
      })
    case 'tool_call':
      return withAssistant(state, (message) => ({
        ...message,
        parts: [...message.parts, {
          kind: 'tool',
          call_id: event.call_id,
          name: event.name,
          args: event.args,
        }],
      }))
    case 'tool_result':
      return withAssistant(state, (message) => {
        const index = message.parts.findIndex(part => part.kind === 'tool' && part.call_id === event.call_id)
        if (index < 0) {
          devWarn('Ignoring tool_result for unknown call', event.call_id)
          return message
        }
        const parts = message.parts.map((part, partIndex) => {
          if (partIndex !== index || part.kind !== 'tool') return part
          const next: ChatToolPartVM = { ...part, ok: event.ok }
          if (event.ok) next.result = event.result
          else next.error = event.error ?? 'The tool failed.'
          return next
        })
        return { ...message, parts }
      })
    case 'approval_required':
      return {
        ...withAssistant(state, (message) => ({
          ...message,
          parts: message.parts.map((part): ChatPartVM => {
            if (part.kind !== 'tool' || part.call_id !== event.call_id) return part
            return {
              ...part,
              pending_revision_id: event.pending_revision.id,
              pending_revision_status: event.pending_revision.status,
            }
          }),
        })),
        pendingApproval: event.pending_revision,
      }
    case 'done':
      return {
        ...withAssistant(state, message => ({ ...message, id: event.message_id, model: event.model })),
        model: event.model,
        streaming: false,
        terminal: true,
      }
    case 'error':
      return {
        ...withAssistant(state, message => ({
          ...message,
          error: { message: event.message, code: event.code },
        })),
        lastError: { message: event.message, code: event.code },
        streaming: false,
        terminal: true,
      }
    default: {
      const unexpected: never = event
      throw new Error(`Unexpected chat event ${JSON.stringify(unexpected)}`)
    }
  }
}
