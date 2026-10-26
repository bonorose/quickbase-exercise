/**
 * HTTP client — the only place that knows about base URL, cookies and CSRF.
 * Endpoint modules in ./endpoints receive this client; nothing above the api/ layer calls fetch.
 *
 *   request  JSON request/response ($fetch)
 *   stream   POST that answers with Server-Sent Events, yielded as parsed JSON events
 */
import { readSSE } from '~/api/sse'

export interface StreamOptions {
  method?: 'GET' | 'POST'
  body?: unknown
  signal?: AbortSignal
}

export interface ApiClient {
  request: typeof $fetch
  stream: <TEvent>(path: string, options?: StreamOptions) => AsyncGenerator<TEvent>
}

export interface ApiClientOptions {
  baseURL: string
  onUnauthorized: () => void
  onCsrfFailure: () => void
}

const UNSAFE = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])
let handlingUnauthorized = false

/** Same shape as $fetch errors ({ status, data }) so utils/apiError.ts handles both. */
export class ApiError extends Error {
  readonly retryAfterSeconds: number | null

  constructor(public readonly status: number, public readonly data: unknown, retryAfter: string | null = null) {
    super(`HTTP ${status}`)
    this.retryAfterSeconds = parseRetryAfter(retryAfter)
  }
}

export function parseRetryAfter(value: string | null): number | null {
  if (!value) return null
  const seconds = Number(value)
  if (Number.isFinite(seconds)) return Math.max(0, Math.ceil(seconds))
  const when = Date.parse(value)
  if (Number.isNaN(when)) return null
  return Math.max(0, Math.ceil((when - Date.now()) / 1000))
}

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  const row = document.cookie.split('; ').find(item => item.startsWith(`${name}=`))
  return row ? decodeURIComponent(row.slice(name.length + 1)) : null
}

function applyCsrf(headers: Headers, method: string) {
  if (!UNSAFE.has(method.toUpperCase())) return
  const token = readCookie('qb_csrf')
  if (token) headers.set('X-CSRF-Token', token)
}

function once(run: () => void) {
  if (handlingUnauthorized) return
  handlingUnauthorized = true
  try {
    run()
  }
  finally {
    setTimeout(() => {
      handlingUnauthorized = false
    }, 1000)
  }
}

function statusLike(err: unknown): number | undefined {
  const value = err as { status?: number, statusCode?: number }
  return value.status ?? value.statusCode
}

export function createApiClient({ baseURL, onUnauthorized, onCsrfFailure }: ApiClientOptions): ApiClient {
  const raw = $fetch.create({
    baseURL,
    credentials: 'include',
    onRequest({ options }) {
      const headers = new Headers(options.headers)
      applyCsrf(headers, String(options.method ?? 'GET'))
      options.headers = headers
    },
    onResponseError({ response }) {
      if (response.status === 401 && !response.url.includes('/auth/login')) once(onUnauthorized)
      const detail = (response._data as { detail?: unknown } | undefined)?.detail
      if (response.status === 403 && detail === 'CSRF check failed') once(onCsrfFailure)
    },
  })

  const request = ((url: Parameters<typeof raw>[0], options?: Parameters<typeof raw>[1]) =>
    raw(url, options).catch((err: unknown) => {
      const status = statusLike(err)
      if (status == null) throw err
      const headers = (err as { response?: { headers?: { get?: (name: string) => string | null } } }).response?.headers
      throw new ApiError(status, (err as { data?: unknown }).data, headers?.get?.('retry-after') ?? null)
    })) as typeof raw

  async function* stream<TEvent>(path: string, { method = 'POST', body, signal }: StreamOptions = {}) {
    const headers = new Headers({ Accept: 'text/event-stream' })
    if (body !== undefined) headers.set('Content-Type', 'application/json')
    applyCsrf(headers, method)
    const response = await fetch(`${baseURL}${path}`, {
      method,
      headers,
      credentials: 'include',
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
    if (!response.ok || !response.body) {
      if (response.status === 401 && !path.includes('/auth/login')) once(onUnauthorized)
      const data = await response.json().catch(() => undefined)
      if (response.status === 403 && data && typeof data === 'object' && data.detail === 'CSRF check failed') {
        once(onCsrfFailure)
      }
      throw new ApiError(response.status, data, response.headers.get('retry-after'))
    }
    yield* readSSE<TEvent>(response.body)
  }

  return { request, stream }
}
