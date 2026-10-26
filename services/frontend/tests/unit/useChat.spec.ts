import { describe, expect, it } from 'vitest'
import { ApiError } from '~/api/client'
import { messageForChatFailure, messageForStreamError } from '~/composables/useChat'

describe('messageForChatFailure', () => {
  it('maps the statuses the composer has to explain', () => {
    expect(messageForChatFailure(new ApiError(409, { detail: 'conflict' }))).toBe('conflict')
    expect(messageForChatFailure(new ApiError(422, { detail: [{ loc: ['body', 'text'], msg: 'too long' }] }))).toBe('too long')
    expect(messageForChatFailure(new ApiError(503, { detail: 'down' }))).toBe('The assistant is unavailable right now')
    expect(messageForChatFailure(new ApiError(500, { code: 'quota_exhausted' }))).toBe('Daily AI quota reached')
    expect(messageForChatFailure(new ApiError(500, { detail: 'boom' }))).toBe('boom')
  })
})

describe('messageForStreamError', () => {
  it('rewrites quota and unavailable codes', () => {
    expect(messageForStreamError({ message: 'quota', code: 'quota_exhausted' })).toBe('Daily AI quota reached')
    expect(messageForStreamError({ message: 'down', code: 'llm_unavailable' })).toBe('The assistant is unavailable right now')
    expect(messageForStreamError({ message: 'kept' })).toBe('kept')
    expect(messageForStreamError(null)).toBeNull()
  })
})
