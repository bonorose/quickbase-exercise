import { describe, expect, it } from 'vitest'
import { pendingFromMessages, toChatMessage, toChatSession, toChatSessionDetail } from '~/services/chat.service'
import type { ChatSessionDetail } from '~/types/api/responses'

const detail: ChatSessionDetail = {
  id: 'sess-1',
  title: '',
  date_created: 1_700_000_000,
  last_activity_at: 1_700_000_100,
  messages: [
    {
      id: 1,
      role: 'user',
      parts: [{ kind: 'text', text: 'What is blocked?' }],
      model: null,
      date_created: 1_700_000_000,
    },
    {
      id: 2,
      role: 'assistant',
      parts: [
        {
          kind: 'tool',
          call_id: 'c1',
          name: 'search_tickets',
          args: { query: 'billing' },
          result: { count: 1, tickets: [{ id: 4, title: 'Billing', status: 'blocked', priority: 'high' }] },
          error: null,
          pending_revision_id: null,
          pending_revision_status: null,
        },
        { kind: 'text', text: 'One ticket is blocked.' },
      ],
      model: 'fake',
      date_created: 1_700_000_010,
    },
  ],
}

describe('chat.service', () => {
  it('maps sessions and folds tool results without provider raw', () => {
    const session = toChatSession({ id: 'sess-1', title: '', date_created: 1, last_activity_at: 2 })
    expect(session.title).toBe('New conversation')
    const view = toChatSessionDetail(detail)
    expect(view.messages).toHaveLength(2)
    expect(view.messages[1]?.parts[0]).toMatchObject({ kind: 'tool', ok: true, name: 'search_tickets' })
    expect(JSON.stringify(view)).not.toContain('model_result')
    expect(JSON.stringify(view)).not.toContain('"raw"')
    expect(toChatMessage(detail.messages[1]!).model).toBe('fake')
  })

  it('treats a pending revision id as a gate until the full record exists', () => {
    const messages = [toChatMessage({
      ...detail.messages[1]!,
      parts: [{
        kind: 'tool',
        call_id: 'c1',
        name: 'mutate_ticket',
        args: {},
        pending_revision_id: 'draft-9',
        pending_revision_status: 'open',
      }],
    })]
    expect(pendingFromMessages(messages)?.id).toBe('draft-9')
  })
})
