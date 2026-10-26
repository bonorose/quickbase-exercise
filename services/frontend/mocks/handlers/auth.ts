import { http, HttpResponse } from 'msw'
import { findUserByEmail, findUserById, toUserResponse } from '../fixtures/users'
import { recordAudit } from '../fixtures/drafts'
import { createMockJwt, identityFromRequest } from '../token'

const api = '*/api/v1'

export const authHandlers = [
  http.post(`${api}/auth/login`, async ({ request }) => {
    const body = await request.json() as { email?: string, password?: string }
    const user = body.email ? findUserByEmail(body.email) : undefined
    if (!user || user.password !== body.password) {
      return HttpResponse.json({ detail: 'Incorrect email or password' }, { status: 401 })
    }
    recordAudit({
      organization_id: user.organization.id,
      actor_type: 'user',
      actor_id: user.id,
      event: 'login',
      session_id: null,
      ticket_id: null,
      pending_revision_id: null,
      payload: {},
    })
    const token = createMockJwt(user)
    return HttpResponse.json(
      { access_token: token, token_type: 'bearer', expires_in: 3600 },
      {
        headers: [
          ['Set-Cookie', `qb_session=${token}; Path=/; SameSite=Lax`],
          ['Set-Cookie', 'qb_csrf=mock-csrf; Path=/; SameSite=Lax'],
        ],
      },
    )
  }),

  http.get(`${api}/auth/me`, ({ request }) => {
    const identity = identityFromRequest(request)
    if (!identity) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    }
    const user = findUserById(identity.userId)
    if (!user) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    }
    return HttpResponse.json(toUserResponse(user))
  }),

  http.post(`${api}/auth/logout`, () => new HttpResponse(null, {
    status: 204,
    headers: [
      ['Set-Cookie', 'qb_session=; Path=/; Max-Age=0'],
      ['Set-Cookie', 'qb_csrf=; Path=/; Max-Age=0'],
    ],
  })),
]
