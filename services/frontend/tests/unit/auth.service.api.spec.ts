import { describe, expect, it, vi } from 'vitest'
import { AuthService, MissingOrganizationError } from '~/services/auth.service'

describe('AuthService', () => {
  it('logs in then loads /auth/me', async () => {
    const api = {
      login: vi.fn(async () => ({ access_token: 'tok', token_type: 'bearer' as const, expires_in: 3600 })),
      me: vi.fn(async () => ({
        id: 12,
        name: 'Excellence Operator One',
        email: 'op1@excellence.qai.local',
        role: 'operator' as const,
        organization: { id: 1, name: 'Excellence' },
      })),
    }
    const service = new AuthService(api)
    const user = await service.login({ email: '  op1@excellence.qai.local  ', password: 'admin123' })
    expect(api.login).toHaveBeenCalledWith({ email: 'op1@excellence.qai.local', password: 'admin123' })
    expect(api.me).toHaveBeenCalledWith()
    expect(user.organization.name).toBe('Excellence')
  })

  it('rejects an account without an organization', async () => {
    const api = {
      login: vi.fn(),
      me: vi.fn(async () => ({
        id: 99,
        name: 'No Team',
        email: 'none@qai.local',
        role: 'operator' as const,
        organization: undefined as never,
      })),
    }
    const service = new AuthService(api)
    await expect(service.currentUser()).rejects.toBeInstanceOf(MissingOrganizationError)
  })
})
