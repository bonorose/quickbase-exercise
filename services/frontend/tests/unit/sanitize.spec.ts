import { describe, expect, it } from 'vitest'
import { inertAssistantText, isDisplayTruncated, truncateForDisplay } from '~/utils/sanitize'

describe('truncateForDisplay', () => {
  it('returns short text unchanged', () => {
    expect(truncateForDisplay('hello')).toBe('hello')
  })

  it('caps long text at 20_000 characters', () => {
    const text = 'a'.repeat(20_050)
    expect(truncateForDisplay(text)).toHaveLength(20_000)
    expect(isDisplayTruncated(text)).toBe(true)
  })
})

describe('inertAssistantText', () => {
  it('replaces markdown and HTML images and drops script tags', () => {
    expect(inertAssistantText('Look: ![leak](https://evil.example/exfil.png) <script>alert(1)</script> <img src="https://evil.example/exfil.png">'))
      .toBe('Look: [image removed]  [image removed]')
  })
})
