import { ApiError } from '~/api/client'
import type { ChatMessageVM } from '~/services/chat.service'
import { getApiErrorMessage, isNotFound, retryAfterSeconds, statusOf } from '~/utils/apiError'
import { toast } from 'vue-sonner'
import { registerAbortController } from '~/utils/abortRegistry'
import { beginTurn, chatStreamReducer, initialChatState, markStopped } from '~/utils/chatStreamReducer'
import type { ChatStreamState } from '~/utils/chatStreamReducer'

export const chatSessionsTick = 'chat:sessions:tick'
export const chatReloadTick = 'chat:reload'

let controller: AbortController | null = null
let generation = 0

function failureCode(err: unknown): string | undefined {
  const data = err instanceof ApiError ? err.data : (err as { data?: { code?: string } }).data
  if (data && typeof data === 'object' && 'code' in data && typeof data.code === 'string') return data.code
  return undefined
}

export function messageForChatFailure(err: unknown): string {
  const status = err instanceof ApiError ? err.status : (err as { status?: number }).status
  const code = failureCode(err)
  if (code === 'quota_exhausted') return 'Daily AI quota reached'
  if (status === 503 || code === 'llm_unavailable') return 'The assistant is unavailable right now'
  if (status === 422) return getApiErrorMessage(err, 'That message could not be sent.')
  if (status === 409) return getApiErrorMessage(err, 'The request could not be completed.')
  return getApiErrorMessage(err, 'The response could not be generated.')
}

export function messageForStreamError(error: { message: string, code?: string } | null): string | null {
  if (!error) return null
  if (error.code === 'quota_exhausted') return 'Daily AI quota reached'
  if (error.code === 'llm_unavailable') return 'The assistant is unavailable right now'
  return error.message
}

function lastUserText(messages: ChatMessageVM[]): string | null {
  const message = [...messages].reverse().find(item => item.role === 'user')
  const part = message?.parts.find(item => item.kind === 'text')
  return part?.kind === 'text' ? part.text : null
}

/**
 * Chat page controller. Turn state is shared by /chat and /chat/:id so replacing
 * the URL on the session event does not abort the stream.
 */
export function useChat(sessionId: Ref<string | null>) {
  const { chat } = useServices()
  const route = useRoute()
  const state = useState<ChatStreamState>('chat:turn', () => initialChatState(sessionId.value))
  const notFound = useState('chat:not-found', () => false)
  const loadError = useState<string | null>('chat:load-error', () => null)
  const composerError = useState<string | null>('chat:composer-error', () => null)
  const retryIn = useState('chat:retry-in', () => 0)
  let cooldownTimer: ReturnType<typeof setInterval> | undefined

  function startCooldown(seconds: number) {
    retryIn.value = seconds
    clearInterval(cooldownTimer)
    const message = `You're sending messages too fast. Try again in ${seconds} s`
    composerError.value = message
    cooldownTimer = setInterval(() => {
      retryIn.value = Math.max(0, retryIn.value - 1)
      if (retryIn.value === 0) {
        clearInterval(cooldownTimer)
        composerError.value = null
        return
      }
      composerError.value = `You're sending messages too fast. Try again in ${retryIn.value} s`
    }, 1000)
  }
  const tick = useState(chatSessionsTick, () => 0)
  const reloadTick = useState(chatReloadTick, () => 0)

  function stop() {
    controller?.abort()
  }

  async function load(id: string | null) {
    stop()
    notFound.value = false
    loadError.value = null
    composerError.value = null
    if (!id) {
      state.value = initialChatState(null)
      return
    }
    try {
      const detail = await chat.getSession(id)
      state.value = {
        ...initialChatState(detail.id),
        messages: detail.messages,
        pendingApproval: detail.pendingApproval,
        terminal: true,
      }
    }
    catch (err) {
      state.value = initialChatState(id)
      if (isNotFound(err)) notFound.value = true
      else loadError.value = getApiErrorMessage(err, 'The conversation could not be loaded.')
    }
  }

  watch(sessionId, (id) => {
    if (state.value.streaming && id && id === state.value.sessionId) return
    void load(id)
  }, { immediate: true })

  watch(reloadTick, () => {
    if (state.value.streaming) return
    void load(sessionId.value ?? state.value.sessionId)
  })

  const messages = computed(() => state.value.messages)
  const status = computed(() => state.value.status)
  const streaming = computed(() => state.value.streaming)
  const pendingApproval = computed(() => state.value.pendingApproval)
  const canSend = computed(() => !state.value.streaming && retryIn.value === 0)
  const error = computed(() => composerError.value ?? messageForStreamError(state.value.lastError))

  async function send(text: string) {
    const trimmed = text.trim()
    if (!trimmed || !canSend.value || trimmed.length > 4000) return
    composerError.value = null
    const current = new AbortController()
    const unregister = registerAbortController(current)
    controller = current
    const mine = ++generation
    state.value = beginTurn(state.value, trimmed)
    try {
      let id = state.value.sessionId ?? sessionId.value
      if (!id) {
        const created = await chat.createSession()
        id = created.id
        state.value = { ...state.value, sessionId: id }
      }
      for await (const event of chat.sendMessage(id, trimmed, current.signal)) {
        if (controller !== current) return
        state.value = chatStreamReducer(state.value, event)
        if (event.type === 'session' && sessionId.value !== event.session_id) {
          await navigateTo(`/chat/${event.session_id}`, { replace: true })
        }
        if (event.type === 'done' || event.type === 'approval_required') tick.value += 1
      }
    }
    catch (err) {
      if (current.signal.aborted) {
        state.value = markStopped(state.value)
      }
      else if (statusOf(err) === 429) {
        const seconds = retryAfterSeconds(err)
        startCooldown(seconds)
        toast.error(`You're sending messages too fast. Try again in ${seconds} s`)
        state.value = { ...state.value, streaming: false, status: null, terminal: true }
      }
      else {
        const mapped = messageForChatFailure(err)
        composerError.value = mapped
        state.value = {
          ...state.value,
          streaming: false,
          status: null,
          terminal: true,
          lastError: { message: mapped },
        }
      }
    }
    finally {
      unregister()
      if (controller === current) controller = null
      if (generation === mine && controller === null && state.value.streaming) {
        state.value = { ...state.value, streaming: false, status: null }
      }
    }
  }

  function retryLast() {
    const text = lastUserText(state.value.messages)
    if (!text || state.value.streaming) return
    const messages = [...state.value.messages]
    while (messages.length > 0 && messages.at(-1)?.role === 'assistant') messages.pop()
    if (messages.at(-1)?.role === 'user') messages.pop()
    state.value = { ...state.value, messages, lastError: null, terminal: false, streaming: false, pendingApproval: state.value.pendingApproval }
    void send(text)
  }

  if (getCurrentScope()) {
    onScopeDispose(() => {
      if (!route.path.startsWith('/chat')) stop()
    })
  }

  return {
    messages,
    status,
    streaming,
    pendingApproval,
    canSend,
    error,
    notFound,
    loadError,
    send,
    stop,
    retryLast,
  }
}
