import type { ErrorResponse } from '~/types/api/responses'

/** Turn a $fetch error into a user-facing message. */
export function getApiErrorMessage(err: unknown, fallback: string): string {
  const e = err as { status?: number, data?: Partial<ErrorResponse> }
  if (e?.status === undefined) return 'Cannot reach the server. Is the backend running?'
  const detail = e.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return fallback
}

/** Only allow same-app absolute paths as post-login redirects. */
export function safeRedirectPath(value: unknown, fallback = '/'): string {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//') ? value : fallback
}
