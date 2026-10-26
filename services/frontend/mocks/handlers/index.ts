import { approvalHandlers } from './approvals'
import { auditHandlers } from './audit'
import { authHandlers } from './auth'
import { chatHandlers } from './chat'
import { ticketHandlers } from './tickets'

export const handlers = [
  ...authHandlers,
  ...ticketHandlers,
  ...chatHandlers,
  ...approvalHandlers,
  ...auditHandlers,
]
