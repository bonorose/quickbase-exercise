import { describe, expect, it } from 'vitest'
import { assertChatStreamEvent } from '../types/chatEvents.test-d'
import type { ChatStreamEvent, PendingRevision } from '~/types/api/responses'

const events: ChatStreamEvent[] = [
  { type: 'session', session_id: 's1' },
  { type: 'status', message: 'thinking' },
  { type: 'delta', text: 'hi' },
  { type: 'tool_call', call_id: 'c1', name: 'search_tickets', args: {} },
  { type: 'tool_result', call_id: 'c1', ok: true },
  { type: 'approval_required', call_id: 'c1', pending_revision: { id: 'd1' } as PendingRevision },
  { type: 'done', message_id: 'm1', model: 'fake' },
  { type: 'error', message: 'boom', code: 'internal' },
]

describe('ChatStreamEvent', () => {
  it('keeps an exhaustive switch over C-20 event types', () => {
    expect(events.map(assertChatStreamEvent)).toEqual([
      'session',
      'status',
      'delta',
      'tool_call',
      'tool_result',
      'approval_required',
      'done',
      'error',
    ])
  })
})
