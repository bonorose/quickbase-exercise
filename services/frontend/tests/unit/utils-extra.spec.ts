import { describe, expect, it } from 'vitest'
import { organizationBadgeClass } from '~/utils/organizationTheme'
import { formatRelativeTime } from '~/utils/relativeTime'
import { ticketFieldLabel } from '~/utils/ticketFieldLabels'
import { navItemsFor } from '~/utils/navItems'

describe('organizationBadgeClass', () => {
  it('maps Excellence and Quantum Workflow', () => {
    expect(organizationBadgeClass('Excellence')).toContain('bg-forest')
    expect(organizationBadgeClass('Quantum Workflow')).toContain('bg-teal-wash')
    expect(organizationBadgeClass('Other Team')).toContain('bg-ink')
  })
})

describe('formatRelativeTime', () => {
  const now = new Date('2026-10-25T12:00:00Z')

  it('formats seconds, minutes, hours, days and months', () => {
    expect(formatRelativeTime(new Date(now.getTime() - 10_000), now)).toMatch(/second/)
    expect(formatRelativeTime(new Date(now.getTime() - 120_000), now)).toMatch(/minute/)
    expect(formatRelativeTime(new Date(now.getTime() - 7_200_000), now)).toMatch(/hour/)
    expect(formatRelativeTime(new Date(now.getTime() - 172_800_000), now)).toMatch(/day/)
    expect(formatRelativeTime(new Date(now.getTime() - 5_184_000_000), now)).toMatch(/month|ago/)
  })
})

describe('ticketFieldLabel', () => {
  it('uses a human label and falls back to the raw field', () => {
    expect(ticketFieldLabel('status')).toBe('Status')
    expect(ticketFieldLabel('unknown')).toBe('unknown')
  })
})

describe('navItems', () => {
  it('enables drafts and audit, and reserves review for team leads', () => {
    expect(navItemsFor('operator').map(item => item.to)).toEqual(['/', '/tickets', '/drafts', '/chat', '/audit'])
    expect(navItemsFor('team_lead').map(item => item.to)).toContain('/review')
  })
})
