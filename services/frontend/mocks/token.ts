import type { FixtureUser } from './fixtures/users'
import { findUserById } from './fixtures/users'

function toBase64Url(value: string): string {
  return btoa(value).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

export function createMockJwt(user: FixtureUser): string {
  const header = toBase64Url(JSON.stringify({ alg: 'none', typ: 'JWT' }))
  const payload = toBase64Url(JSON.stringify({
    sub: String(user.id),
    organization_id: user.organization.id,
    role: user.role,
    jti: `mock-${user.id}`,
    exp: Math.floor(Date.now() / 1000) + 3600,
  }))
  return `${header}.${payload}.mock`
}

export function identityFromRequest(request: Request): { userId: number, organizationId: number } | null {
  const header = request.headers.get('Authorization')
  const cookie = request.headers.get('cookie') ?? ''
  const session = cookie.split(';').map(item => item.trim()).find(item => item.startsWith('qb_session='))
  const token = header?.startsWith('Bearer ')
    ? header.slice(7)
    : session ? decodeURIComponent(session.slice('qb_session='.length)) : ''
  if (!token) return null
  const payload = token.split('.')[1]
  if (!payload) return null
  try {
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const json = JSON.parse(atob(base64 + '='.repeat((4 - (base64.length % 4)) % 4))) as {
      sub?: string
      organization_id?: number
    }
    const userId = Number(json.sub)
    const user = findUserById(userId)
    if (!user) return null
    return { userId: user.id, organizationId: user.organization.id }
  }
  catch {
    return null
  }
}
