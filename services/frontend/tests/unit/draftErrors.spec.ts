import { describe, expect, it } from 'vitest'
import { ApiError } from '~/api/client'
import { claimConflictOwner, messageForDraftFailure } from '~/utils/apiError'

describe('draft contract errors', () => {
  it('maps C-10 and C-18 statuses the editor has to explain', () => {
    expect(messageForDraftFailure(new ApiError(410, { detail: 'Pending revision has expired' })))
      .toBe('This draft has expired. Ask the assistant to propose it again.')
    expect(messageForDraftFailure(new ApiError(409, { detail: 'Ticket changed since this draft was saved' })))
      .toBe('Ticket changed, review and save again.')
    expect(messageForDraftFailure(new ApiError(403, { detail: 'A tainted pending revision can only be approved by a team lead' })))
      .toBe('A team lead has to approve this draft.')
    expect(messageForDraftFailure(new ApiError(422, { detail: [{ loc: ['body', 'changed_contents', 'description'], msg: 'Extra inputs are not permitted' }] })))
      .toBe('Extra inputs are not permitted')
  })

  it('reads the C-17 409 owner', () => {
    expect(claimConflictOwner(new ApiError(409, {
      detail: 'being worked on by Ada',
      pending_revision_id: 'draft-1',
      owner: { id: 3, name: 'Ada' },
    }))).toEqual({ id: 3, name: 'Ada' })
    expect(claimConflictOwner(new ApiError(409, { detail: 'Ticket changed since this draft was saved' }))).toBeNull()
  })
})
