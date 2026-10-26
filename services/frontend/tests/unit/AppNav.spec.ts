import { describe, expect, it } from 'vitest'
import { isNavItemActive, navItemsFor } from '~/utils/navItems'

describe('AppNav', () => {
  it('shows drafts and audit, and keeps review for team leads', () => {
    const operator = navItemsFor('operator').map(item => item.label)
    const lead = navItemsFor('team_lead').map(item => item.label)
    expect(operator).toEqual(['Dashboard', 'Tickets', 'Drafts', 'Chat', 'Audit'])
    expect(lead).toContain('Review')
    expect(isNavItemActive('/tickets', '/tickets')).toBe(true)
    expect(isNavItemActive('/tickets', '/')).toBe(false)
    expect(isNavItemActive('/', '/')).toBe(true)
    expect(isNavItemActive('/drafts', '/drafts')).toBe(true)
  })
})
