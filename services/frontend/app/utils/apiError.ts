import { ApiError, parseRetryAfter } from '~/api/client'
import type { ActorRef, ErrorResponse } from '~/types/api/responses'

function errorPayload(err: unknown): Partial<ErrorResponse> | undefined {
  if (err instanceof ApiError && err.data && typeof err.data === 'object') return err.data as Partial<ErrorResponse>
  const data = (err as { data?: Partial<ErrorResponse> }).data
  return data && typeof data === 'object' ? data : undefined
}

/** Turn a $fetch error into a user-facing message. */
export function getApiErrorMessage(err: unknown, fallback: string): string {
  if (statusOf(err) === undefined) return 'Can\'t reach qAI. Check your connection or try again'
  const detail = errorPayload(err)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return fallback
}

export function messageForDraftFailure(err: unknown): string {
  const status = statusOf(err)
  if (status === 410) return 'This draft has expired. Ask the assistant to propose it again.'
  if (status === 409) return 'Ticket changed, review and save again.'
  if (status === 403) return 'A team lead has to approve this draft.'
  return getApiErrorMessage(err, 'Could not update that draft.')
}

export function claimConflictOwner(err: unknown): ActorRef | null {
  if (statusOf(err) !== 409) return null
  const owner = errorPayload(err)?.owner
  if (!owner || typeof owner.id !== 'number' || typeof owner.name !== 'string') return null
  return owner
}

/** Only allow same-app absolute paths as post-login redirects. */
export function safeRedirectPath(value: unknown, fallback = '/'): string {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//') ? value : fallback
}

export function statusOf(err: unknown): number | undefined {
  if (err instanceof ApiError) return err.status
  const e = err as { status?: number, statusCode?: number }
  return e?.status ?? e?.statusCode
}

/** Seconds to wait after HTTP 429. Missing Retry-After becomes 30. */
export function retryAfterSeconds(err: unknown): number {
  if (statusOf(err) !== 429) return 0
  if (err instanceof ApiError && err.retryAfterSeconds != null) return err.retryAfterSeconds
  const headers = (err as { response?: { headers?: { get?: (name: string) => string | null } } }).response?.headers
  return parseRetryAfter(headers?.get?.('retry-after') ?? null) ?? 30
}

/** True for both `$fetch` errors and `ApiError` with HTTP 404. */
export function isNotFound(err: unknown): boolean {
  return statusOf(err) === 404
}
