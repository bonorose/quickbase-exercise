import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { getTicket, ticketsForOrganization } from '../../mocks/fixtures/tickets'
import { users } from '../../mocks/fixtures/users'
import { ticketHandlers } from '../../mocks/handlers/tickets'
import { server } from '../../mocks/server'
import { iterateScriptedEvents, sseScenarios } from '../../mocks/sse'
import { createMockJwt, identityFromRequest } from '../../mocks/token'

beforeAll(() => server.listen({ onUnhandledFrame: 'bypass' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('MSW ticket isolation', () => {
  it('returns no ticket when the id belongs to another organization', () => {
    const excellence = users.find(user => user.email === 'op1@excellence.qai.local')!
    const identity = identityFromRequest(new Request('http://localhost/api/v1/tickets/101', {
      headers: { Authorization: `Bearer ${createMockJwt(excellence)}` },
    }))
    expect(identity?.organizationId).toBe(1)
    expect(getTicket(101, identity!.organizationId)).toBeUndefined()
    expect(getTicket(101, 2)).toBeDefined()
  })

  it('paginates a tenant list', () => {
    const items = ticketsForOrganization(1)
    expect(items).toHaveLength(12)
    expect(items.every(item => item.id < 100)).toBe(true)
    expect(items.slice(0, 5)).toHaveLength(5)
  })
})

describe('SSE helper', () => {
  it('yields the mutate-requires-approval grammar', async () => {
    const types: string[] = []
    for await (const event of iterateScriptedEvents(sseScenarios['mutate-requires-approval']!)) {
      types.push(event.type)
    }
    expect(types).toEqual(['session', 'status', 'tool_call', 'tool_result', 'approval_required', 'done'])
  })
})

describe('ticket handlers export', () => {
  it('registers list and detail routes', () => {
    expect(ticketHandlers.length).toBeGreaterThanOrEqual(2)
  })
})
