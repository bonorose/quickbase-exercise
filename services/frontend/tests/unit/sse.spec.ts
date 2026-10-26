import { describe, expect, it } from 'vitest'
import { readSSE } from '~/api/sse'

function streamFromChunks(chunks: string[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder()
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
      controller.close()
    },
  })
}

async function collect<T>(stream: ReadableStream<Uint8Array>): Promise<T[]> {
  const events: T[] = []
  for await (const event of readSSE<T>(stream)) events.push(event)
  return events
}

describe('readSSE', () => {
  it('yields one event when a frame is split across chunks', async () => {
    const events = await collect(streamFromChunks([
      'data: {"type":"status","mes',
      'sage":"hello"}\n\n',
    ]))
    expect(events).toEqual([{ type: 'status', message: 'hello' }])
  })

  it('normalises CRLF delimiters', async () => {
    const events = await collect(streamFromChunks([
      'data: {"type":"delta","text":"a"}\r\n\r\n',
    ]))
    expect(events).toEqual([{ type: 'delta', text: 'a' }])
  })

  it('joins multi-line data: fields', async () => {
    const events = await collect(streamFromChunks([
      'data: {"text":\n',
      'data: "ab"}\n\n',
    ]))
    expect(events).toEqual([{ text: 'ab' }])
  })
})
