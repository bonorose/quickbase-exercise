import { expectTypeOf } from 'vitest'
import type { ChatStreamEvent } from '~/types/api/responses'

/** C-20 v1.2 — no extra event names, and the switch stays exhaustive. */
type ChatStreamEventType = ChatStreamEvent['type']

expectTypeOf<ChatStreamEventType>().toEqualTypeOf<
  'session' | 'status' | 'delta' | 'tool_call' | 'tool_result' | 'approval_required' | 'done' | 'error'
>()

export function assertChatStreamEvent(event: ChatStreamEvent): ChatStreamEvent['type'] {
  switch (event.type) {
    case 'session':
      return event.type
    case 'status':
      return event.type
    case 'delta':
      return event.type
    case 'tool_call':
      return event.type
    case 'tool_result':
      return event.type
    case 'approval_required':
      return event.type
    case 'done':
      return event.type
    case 'error':
      return event.type
    default: {
      const _never: never = event
      return _never
    }
  }
}
