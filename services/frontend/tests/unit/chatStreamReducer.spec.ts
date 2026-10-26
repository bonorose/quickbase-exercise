import { describe, expect, it, vi } from 'vitest'
import type { PendingRevision } from '~/types/api/responses'
import { sseScenarios } from '../../mocks/sse'
import { beginTurn, chatStreamReducer, initialChatState } from '~/utils/chatStreamReducer'
import type { ChatStreamState } from '~/utils/chatStreamReducer'

function play(events: Parameters<typeof chatStreamReducer>[1][], start = beginTurn(initialChatState(), 'hi')): ChatStreamState {
  return events.reduce((state, event) => chatStreamReducer(state, event), start)
}

const pending = {
  id: 'draft-4',
  status: 'open',
} as PendingRevision

describe('chatStreamReducer', () => {
  it('folds each scripted read-path scenario', () => {
    const plain = play(sseScenarios['plain-answer']!)
    expect(plain.sessionId).toBe('sess-plain')
    expect(plain.streaming).toBe(false)
    expect(plain.model).toBe('gemini-3.8-flash')
    expect(plain.messages.at(-1)?.parts).toEqual([{ kind: 'text', text: 'Here is a plain answer.' }])
    expect(plain.status).toBeNull()

    const search = play(sseScenarios['search-then-answer']!)
    const tool = search.messages.at(-1)?.parts.find(part => part.kind === 'tool')
    expect(tool).toMatchObject({ name: 'search_tickets', ok: true })
    expect(search.messages.at(-1)?.parts.at(-1)).toEqual({ kind: 'text', text: 'I found a billing ticket.' })

    const failed = play(sseScenarios['llm-error']!)
    expect(failed.lastError?.code).toBe('llm_unavailable')
    expect(failed.streaming).toBe(false)

    const quota = play(sseScenarios.quota!)
    expect(quota.lastError?.code).toBe('quota_exhausted')
  })

  it('keeps text before and after a tool call in order', () => {
    const state = play([
      { type: 'delta', text: 'Before' },
      { type: 'tool_call', call_id: 'c1', name: 'search_tickets', args: { query: 'billing' } },
      { type: 'delta', text: 'After' },
    ])
    expect(state.messages.at(-1)?.parts).toEqual([
      { kind: 'text', text: 'Before' },
      { kind: 'tool', call_id: 'c1', name: 'search_tickets', args: { query: 'billing' } },
      { kind: 'text', text: 'After' },
    ])
  })

  it('records approval without ending the stream, then done stops it', () => {
    const state = play([
      { type: 'tool_call', call_id: 'c2', name: 'mutate_ticket', args: { id: 4 } },
      { type: 'approval_required', call_id: 'c2', pending_revision: pending },
      { type: 'done', message_id: 'msg-1', model: 'fake' },
    ])
    expect(state.pendingApproval?.id).toBe('draft-4')
    expect(state.streaming).toBe(false)
    expect(state.messages.at(-1)?.id).toBe('msg-1')
    expect(state.messages.at(-1)?.parts[0]).toMatchObject({ pending_revision_id: 'draft-4', pending_revision_status: 'open' })
  })

  it('ignores an unknown tool result and events after a terminal event', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const open = play([
      { type: 'tool_call', call_id: 'c1', name: 'search_tickets', args: {} },
      { type: 'tool_result', call_id: 'missing', ok: false, error: 'nope' },
    ])
    expect(open.messages.at(-1)?.parts).toHaveLength(1)
    const done = chatStreamReducer(open, { type: 'done', message_id: 'm', model: 'fake' })
    const ignored = chatStreamReducer(done, { type: 'delta', text: 'late' })
    expect(ignored.messages.at(-1)?.parts).toEqual(done.messages.at(-1)?.parts)
    expect(warn).toHaveBeenCalled()
    warn.mockRestore()
  })

  it('clears the status line when the next event arrives', () => {
    const waiting = play([{ type: 'status', message: 'Searching tickets…' }])
    expect(waiting.status).toBe('Searching tickets…')
    expect(play([{ type: 'status', message: 'Searching tickets…' }, { type: 'delta', text: 'Hi' }]).status).toBeNull()
  })

  it('stores a tool error and leaves a successful result without description text in the part', () => {
    const state = play([
      { type: 'tool_call', call_id: 'c1', name: 'search_tickets', args: { query: 'billing' } },
      { type: 'tool_result', call_id: 'c1', ok: false, error: 'Ticket not found' },
    ])
    expect(state.messages.at(-1)?.parts[0]).toMatchObject({ ok: false, error: 'Ticket not found' })
  })
})
