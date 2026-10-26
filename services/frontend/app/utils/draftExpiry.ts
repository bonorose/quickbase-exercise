/**
 * Milliseconds left before a draft expires, or null when it never expires.
 *
 * Uses only server timestamps for the window (`expires_at - server_time`), then subtracts the
 * time elapsed on this browser since the draft was received, so a skewed client clock does
 * not change the countdown.
 */
export function draftRemainingMs(
  draft: { expires_at: number | null, server_time: number },
  receivedAtMs: number,
  nowMs: number,
): number | null {
  if (draft.expires_at == null) return null
  return (draft.expires_at - draft.server_time) * 1000 - (nowMs - receivedAtMs)
}
