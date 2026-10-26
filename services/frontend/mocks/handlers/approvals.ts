import { http, HttpResponse } from 'msw'
import { claimDraft, decideDraft, getDraft, listDrafts, saveDraft } from '../fixtures/drafts'
import { findUserById } from '../fixtures/users'
import { identityFromRequest } from '../token'

const api = '*/api/v1'

function userFrom(request: Request) {
  const identity = identityFromRequest(request)
  if (!identity) return null
  return findUserById(identity.userId) ?? null
}

function present<T extends { organization_id?: number, user_id?: number }>(draft: T) {
  const { organization_id: _organizationId, user_id: _userId, ...body } = draft
  return body
}

export const approvalHandlers = [
  http.get(`${api}/pending-revisions`, ({ request }) => {
    const user = userFrom(request)
    if (!user) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const scope = new URL(request.url).searchParams.get('scope') ?? 'mine'
    if (scope === 'lead_queue' && user.role !== 'team_lead') {
      return HttpResponse.json({ detail: 'Team lead role is required' }, { status: 403 })
    }
    return HttpResponse.json(listDrafts(user, scope).map(present))
  }),

  http.get(`${api}/pending-revisions/:id`, ({ request, params }) => {
    const user = userFrom(request)
    if (!user) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const draft = getDraft(String(params.id), user)
    if (!draft) return HttpResponse.json({ detail: 'Pending revision not found' }, { status: 404 })
    return HttpResponse.json(present(draft))
  }),

  http.post(`${api}/tickets/:id/pending-revisions`, async ({ request, params }) => {
    const user = userFrom(request)
    if (!user) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const body = await request.json() as { action?: 'update' | 'delete', changed_contents?: Record<string, unknown> }
    if (body.changed_contents && 'description' in body.changed_contents) {
      return HttpResponse.json({ detail: [{ loc: ['body', 'changed_contents', 'description'], msg: 'Extra inputs are not permitted' }] }, { status: 422 })
    }
    if (body.action !== 'update' && body.action !== 'delete') {
      return HttpResponse.json({ detail: [{ loc: ['body', 'action'], msg: 'Field required' }] }, { status: 422 })
    }
    const result = claimDraft(user, Number(params.id), body.action, body.changed_contents)
    if (result.error === 'missing') return HttpResponse.json({ detail: 'Ticket not found' }, { status: 404 })
    if (result.error === 'conflict') return HttpResponse.json(result.body, { status: 409 })
    return HttpResponse.json(present(result.draft), { status: 201 })
  }),

  http.put(`${api}/pending-revisions/:id`, async ({ request, params }) => {
    const user = userFrom(request)
    if (!user) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const body = await request.json() as { action?: 'update' | 'delete', changed_contents?: Record<string, unknown> }
    const saved = saveDraft(user, String(params.id), body.changed_contents ?? {}, body.action)
    if (saved === 'forbidden') return HttpResponse.json({ detail: 'Only the owner can save this pending revision' }, { status: 403 })
    if (!saved) return HttpResponse.json({ detail: 'Pending revision not found' }, { status: 404 })
    return HttpResponse.json(present(saved))
  }),

  http.post(`${api}/pending-revisions/:id/approve`, async ({ request, params }) => {
    const user = userFrom(request)
    if (!user) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const body = await request.json() as { action?: 'update' | 'delete', changed_contents?: Record<string, unknown> }
    const decided = decideDraft(user, String(params.id), 'executed', body.changed_contents, body.action)
    if (decided === 'forbidden') {
      return HttpResponse.json({ detail: 'A tainted pending revision can only be approved by a team lead' }, { status: 403 })
    }
    if (!decided) return HttpResponse.json({ detail: 'Pending revision not found' }, { status: 404 })
    return HttpResponse.json({ pending_revision: present(decided), ticket: { id: decided.ticket.id, title: decided.ticket.title } })
  }),

  http.post(`${api}/pending-revisions/:id/reject`, async ({ request, params }) => {
    const user = userFrom(request)
    if (!user) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const body = await request.json() as { reason?: string }
    const decided = decideDraft(user, String(params.id), 'rejected', undefined, undefined)
    if (!decided || decided === 'forbidden') return HttpResponse.json({ detail: 'Pending revision not found' }, { status: 404 })
    return HttpResponse.json(present({ ...decided, result: body.reason ? { reason: body.reason } : {} }))
  }),
]
