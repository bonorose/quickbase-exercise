import { HttpResponse } from 'msw'
import type { ChatStreamEvent } from '~/types/api/responses'

export function encodeSseFrame(event: ChatStreamEvent): string {
  return `data: ${JSON.stringify(event)}\n\n`
}

export async function* iterateScriptedEvents(
  events: ChatStreamEvent[],
  delayMs = 0,
): AsyncGenerator<ChatStreamEvent> {
  for (const event of events) {
    if (delayMs > 0) {
      await new Promise(resolve => setTimeout(resolve, delayMs))
    }
    yield event
  }
}

export const sseScenarios: Record<string, ChatStreamEvent[]> = {
  'plain-answer': [
    { type: 'session', session_id: 'sess-plain' },
    { type: 'status', message: 'Waiting for gemini-3.8-flash…' },
    { type: 'delta', text: 'Here is a plain answer.' },
    { type: 'done', message_id: 'msg-plain', model: 'gemini-3.8-flash' },
  ],
  'search-then-answer': [
    { type: 'session', session_id: 'sess-search' },
    { type: 'status', message: 'Searching tickets…' },
    { type: 'tool_call', call_id: 'call-1', name: 'search_tickets', args: { query: 'billing' } },
    { type: 'tool_result', call_id: 'call-1', ok: true, result: { items: [{ id: 4, title: 'Excellence ticket 4 billing' }] } },
    { type: 'delta', text: 'I found a billing ticket.' },
    { type: 'done', message_id: 'msg-search', model: 'gemini-3.8-flash' },
  ],
  'mutate-requires-approval': [
    { type: 'session', session_id: 'sess-mutate' },
    { type: 'status', message: 'Preparing a change…' },
    { type: 'tool_call', call_id: 'call-2', name: 'mutate_ticket', args: { id: 4, action: 'update', fields: { status: 'blocked' } } },
    { type: 'tool_result', call_id: 'call-2', ok: true, result: { pending_revision_id: 'draft-4', status: 'open' } },
    {
      type: 'approval_required',
      call_id: 'call-2',
      pending_revision: {
        id: 'draft-4',
        ticket: { id: 4, title: 'Excellence ticket 4 billing' },
        action: 'update',
        origin: 'agent',
        owner: { id: 12, name: 'Excellence Operator One' },
        session_id: 'sess-mutate',
        previous_revision_id: 'rev-4',
        changed_contents: { status: 'blocked' },
        diff: { status: { from: 'open', to: 'blocked' } },
        tainted: false,
        status: 'open',
        expires_at: Math.floor(Date.now() / 1000) + 600,
        server_time: Math.floor(Date.now() / 1000),
        decided_by: null,
        decided_at: null,
        date_created: Math.floor(Date.now() / 1000),
        date_updated: Math.floor(Date.now() / 1000),
        result: null,
      },
    },
    { type: 'done', message_id: 'msg-mutate', model: 'gemini-3.8-flash' },
  ],
  'llm-error': [
    { type: 'session', session_id: 'sess-error' },
    { type: 'error', message: 'The assistant is unavailable.', code: 'llm_unavailable' },
  ],
  quota: [
    { type: 'session', session_id: 'sess-quota' },
    { type: 'error', message: 'Daily AI quota reached.', code: 'quota_exhausted' },
  ],
}

export function sseResponse(events: ChatStreamEvent[], delayMs = 0) {
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const encoder = new TextEncoder()
      for (const event of events) {
        if (delayMs > 0) {
          await new Promise(resolve => setTimeout(resolve, delayMs))
        }
        controller.enqueue(encoder.encode(encodeSseFrame(event)))
      }
      controller.close()
    },
  })
  return new HttpResponse(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
    },
  })
}
