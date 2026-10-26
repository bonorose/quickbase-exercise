/**
 * Minimal Server-Sent Events reader for fetch() responses.
 * EventSource can't send POST bodies or an Authorization header, so streams use fetch + this parser.
 * Each frame is `data: <json>` lines terminated by a blank line (see backend core/sse.py).
 */
export async function* readSSE<T>(body: ReadableStream<Uint8Array>): AsyncGenerator<T> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n?/g, '\n')
      let boundary: number
      while ((boundary = buffer.indexOf('\n\n')) !== -1) {
        const frame = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        const data = frame
          .split('\n')
          .filter(line => line.startsWith('data:'))
          .map(line => line.slice(5).replace(/^ /, ''))
          .join('\n')
        if (data) yield JSON.parse(data) as T
      }
    }
  }
  finally {
    // Runs on normal end, on error, and when the consumer stops early (break / abort)
    reader.releaseLock()
  }
}
