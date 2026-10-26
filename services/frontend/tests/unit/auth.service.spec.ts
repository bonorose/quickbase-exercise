import { describe, expect, it } from 'vitest'
import { MissingOrganizationError, toUser } from '~/services/auth.service'
import type { UserResponse } from '~/types/api/responses'

const quantum: UserResponse = {
  id: 22,
  name: 'Quantum Operator One',
  email: 'op1@quantum.qai.local',
  role: 'operator',
  organization: { id: 2, name: 'Quantum Workflow' },
}

describe('toUser', () => {
  it('maps name to fullName and initials', () => {
    const user = toUser(quantum)
    expect(user.fullName).toBe('Quantum Operator One')
    expect(user.initials).toBe('QO')
    expect(user.organization.name).toBe('Quantum Workflow')
    expect(user.role).toBe('operator')
  })

  it('throws when the account has no organization', () => {
    expect(() => toUser({ ...quantum, organization: undefined as never })).toThrow(MissingOrganizationError)
    expect(() => toUser({ ...quantum, organization: undefined as never })).toThrow('Your account is not assigned to a team')
  })
})
