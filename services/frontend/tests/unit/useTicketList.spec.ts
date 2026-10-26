import { describe, expect, it } from 'vitest'
import { parsePage, parsePriority, parseSort, parseStatus, parseTicketId } from '~/composables/useTicketList'

describe('useTicketList query parsing', () => {
  it('reads C-03 filters from the URL', () => {
    expect(parseStatus('open')).toBe('open')
    expect(parseStatus('in_progress')).toBeUndefined()
    expect(parsePriority('critical')).toBe('critical')
    expect(parsePriority('urgent')).toBeUndefined()
    expect(parseSort('-priority')).toBe('-priority')
    expect(parseSort('-updated_at')).toBe('-date_updated')
    expect(parsePage('2')).toBe(2)
    expect(parsePage('0')).toBe(1)
    expect(parseTicketId('12')).toBe(12)
    expect(parseTicketId('0')).toBeNull()
  })
})
